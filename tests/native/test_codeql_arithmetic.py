#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Compile allocation expressions from the shipped sources at large dimensions."""
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "native/nfiq1/upstream/mindtct/src/lib/mindtct"

class ArithmeticRegression(unittest.TestCase):
    def test_allocation_products_exceed_signed_int_without_overflow(self):
        cases = [("binar.c", "bdata", "bw", "bh", 1),
                 ("maps.c", "pmap", "iw", "ih", 4),
                 ("maps.c", "omap", "mw", "mh", 4),
                 ("quality.c", "QualMap", "map_w", "map_h", 4)]
        for filename, target, width, height, size in cases:
            source = (SOURCE / filename).read_text()
            expressions = re.findall(r"\b" + target + r"\s*=\s*\([^;]*?\)malloc\(([^;]+)\);", source)
            self.assertTrue(expressions, filename)
            for expression in expressions:
                with self.subTest(file=filename, expression=expression), tempfile.TemporaryDirectory() as folder:
                    c = Path(folder) / "size.c"
                    c.write_text("#include <stddef.h>\n#include <stdint.h>\nint main(void) {\n"
                                 + f"volatile int {width}=65536, {height}=65536;\n"
                                 + f"size_t result = {expression};\n"
                                 + f"return result != UINT64_C({65536 * 65536 * size});\n}}\n")
                    exe = Path(folder) / "size"
                    subprocess.run(["cc", "-fsanitize=undefined", "-fno-sanitize-recover=all", str(c), "-o", str(exe)], check=True)
                    subprocess.run([str(exe)], check=True)

    def test_direction_map_copy_uses_the_full_allocation_size(self):
        source = (SOURCE / "maps.c").read_text()
        expression = re.search(r"memcpy\(direction_map, omap, (.+)\);", source).group(1)
        with tempfile.TemporaryDirectory() as folder:
            c = Path(folder) / "copy.c"
            # Intercept memcpy so the real count expression is exercised without
            # allocating or touching a 16 GiB buffer.
            c.write_text("#include <stddef.h>\n#include <stdint.h>\n"
                         "static size_t copied;\n"
                         "static void *record_copy(void *d, const void *s, size_t n) { copied=n; return d; }\n"
                         "#define memcpy record_copy\n"
                         "int main(void) { volatile int mw=65536, mh=65536;\n"
                         "int *direction_map=0, *omap=0;\n"
                         + f"memcpy(direction_map, omap, {expression});\n"
                         "return copied != UINT64_C(17179869184);}\n")
            exe = Path(folder) / "copy"
            subprocess.run(["cc", "-fsanitize=undefined", "-fno-sanitize-recover=all", str(c), "-o", str(exe)], check=True)
            subprocess.run([str(exe)], check=True)

    def test_float_comparison_product_stays_finite(self):
        source = (ROOT / "native/nfiq1/upstream/commonnbis/src/lib/clapck/slagts.c").read_text()
        expressions = re.findall(r"else if \(dabs\(temp\) > (.*)\) \{", source)
        self.assertEqual(len(expressions), 4)
        for expression in expressions:
            with tempfile.TemporaryDirectory() as folder:
                c = Path(folder) / "product.c"
                c.write_text("#include <math.h>\nint main(void) {\n"
                             "volatile float absak=1e30f, bignum=1e30f;\n"
                             + f"double product = {expression};\n"
                             "return !isfinite(product) || product < 1e59;\n}\n")
                exe = Path(folder) / "product"
                subprocess.run(["cc", str(c), "-o", str(exe)], check=True)
                subprocess.run([str(exe)], check=True)

    def test_pointer_difference_format(self):
        source = (ROOT / "native/nfiq1/upstream/pcasys/src/lib/mlp/e_and_g.c").read_text()
        fmt = re.search(r'fprintf\(fp_long_outfile, ("%6[^"\n]+")', source).group(1)
        with tempfile.TemporaryDirectory() as folder:
            c = Path(folder) / "format.c"
            c.write_text('#include <stdio.h>\n#include <stddef.h>\nint main(void) {\n'
                         + f'printf({fmt}, (ptrdiff_t)1, 2, 82, 3); return 0;}}\n')
            subprocess.run(["cc", "-Werror=format", "-fsyntax-only", str(c)], check=True)

    def test_eigen_failure_indices_and_allocation_ownership(self):
        source = (ROOT / "native/nfiq1/upstream/pcasys/src/lib/pca/eigen.c").read_text()
        function = source[source.index("void diag_mat_eigen("):]
        # Exercise the actual legacy routine with a deterministic LAPACK failure.
        harness = r"""
#include <stdio.h>
#include <stdlib.h>
#include <stddef.h>
#define max(a,b) ((a) > (b) ? (a) : (b))
static int live;
static void *tracked_malloc(size_t n) { void *p=malloc(n); if(p) ++live; return p; }
static void tracked_free(void *p) { if(p) --live; free(p); }
#define malloc tracked_malloc
#define free tracked_free
static int ilaenv_(int *i, ...) { return 1; }
static float slamch_(char *s) { return 0.00001f; }
static void sswap_(const int *n, float *a, int *ai, float *b, int *bi) {}
static void ssyevx_(char *v, char *i, char *l, const int *order, float *mat,
 int *lda, float *vl, float *vu, int *il, int *iu, float *tol, int *found,
 float *values, float *vectors, const int *ldz, float *work, int *lwork,
 int *iwork, int *failures, int *info) {
 *found=3; *info=1; failures[0]=1;
 for(int j=0;j<3;++j) values[j]=(float)j;
}
"""
        main = r"""
int main(void) {
 float mat[16]={0}, *values, *vectors; int *failures, info;
 diag_mat_eigen(4,mat,3,&values,&vectors,&failures,&info);
 int wrong = info != 1 || failures[0] != 2;
 free(values); free(vectors); free(failures);
 return wrong || live != 0;
}
"""
        with tempfile.TemporaryDirectory() as folder:
            c = Path(folder) / "eigen.c"
            c.write_text(harness + function + main)
            exe = Path(folder) / "eigen"
            subprocess.run(["cc", "-fsanitize=undefined", "-fno-sanitize-recover=all", str(c), "-o", str(exe)], check=True)
            subprocess.run([str(exe)], check=True)

    def test_eigen_caller_keeps_every_converged_vector(self):
        source = (ROOT / "native/nfiq1/upstream/pcasys/src/lib/pca/eigen.c").read_text()
        functions = source[source.index("void eigen("):]
        harness = r"""
#include <stdio.h>
#include <stdlib.h>
#include <stddef.h>
#define max(a,b) ((a) > (b) ? (a) : (b))
static int live, failure_count;
static int failures_in[4];
static void *tracked_malloc(size_t n) { void *p=calloc(1,n); if(p) ++live; return p; }
static void tracked_free(void *p) { if(p) --live; free(p); }
#define malloc tracked_malloc
#define free tracked_free
void diag_mat_eigen(const int, float *, const int, float **, float **, int **, int *);
static int ilaenv_(int *i, ...) { return 1; }
static float slamch_(char *s) { return 0.00001f; }
static void sswap_(const int *n, float *a, int *ai, float *b, int *bi) {
 for(int k=0;k<*n;++k) { float t=a[k * *ai]; a[k * *ai]=b[k * *bi]; b[k * *bi]=t; }
}
static void ssyevx_(char *v, char *i, char *l, const int *order, float *mat,
 int *lda, float *vl, float *vu, int *il, int *iu, float *tol, int *found,
 float *values, float *vectors, const int *ldz, float *work, int *lwork,
 int *iwork, int *failures, int *info) {
 *found=4; *info=failure_count;
 for(int j=0;j<failure_count;++j) failures[j]=failures_in[j];
 for(int j=0;j<4;++j) {
  values[j]=(float)(j+1);
  for(int k=0;k<*order;++k) vectors[j * *order+k]=(float)(100*j+k);
 }
}
"""
        main = r"""
int main(void) {
 float mat[25]={0}, *values, *vectors; int found;
 /* Two failed columns become indices 1 and 3 in descending vector order. */
 failure_count=2; failures_in[0]=1; failures_in[1]=3;
 eigen(4,&found,&vectors,&values,mat,5);
 if(found!=2 || values[0]!=4 || values[1]!=2) return 1;
 for(int k=0;k<5;++k) if(vectors[k]!=300+k || vectors[5+k]!=100+k) return 2;
 free(values); free(vectors);
 if(live) return 3;
 /* One failure at the first returned column must not truncate the tail. */
 failure_count=1; failures_in[0]=4;
 eigen(4,&found,&vectors,&values,mat,5);
 if(found!=3 || values[0]!=3 || values[1]!=2 || values[2]!=1) return 4;
 free(values); free(vectors);
 if(live) return 5;
 failure_count=0;
 eigen(4,&found,&vectors,&values,mat,5);
 if(found!=4 || values[0]!=4 || values[3]!=1) return 6;
 free(values); free(vectors);
 return live != 0;
}
"""
        with tempfile.TemporaryDirectory() as folder:
            c = Path(folder) / "eigen-caller.c"
            c.write_text(harness + functions + main)
            exe = Path(folder) / "eigen-caller"
            subprocess.run(["cc", "-fsanitize=undefined", "-fno-sanitize-recover=all", str(c), "-o", str(exe)], check=True)
            subprocess.run([str(exe)], check=True)

if __name__ == "__main__":
    unittest.main()
