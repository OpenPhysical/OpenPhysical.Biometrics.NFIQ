#include <nfiq.h>
#include <stdio.h>
#include <stdlib.h>
int main(int argc, char **argv) {
  if (argc != 2 && argc != 4)
    return 2;
  FILE *f = fopen(argv[1], "rb");
  if (!f)
    return 3;
  int width = argc == 4 ? atoi(argv[2]) : 512;
  int height = argc == 4 ? atoi(argv[3]) : 512;
  unsigned char *p = malloc((size_t)width * height);
  if (fread(p, 1, (size_t)width * height, f) != ((size_t)width * height))
    return 4;
  fclose(f);
  int q = 0, flag = 0;
  float c = 0;
  int ret = comp_nfiq(&q, &c, p, width, height, 8, 500, &flag);
  printf("%d %d %.9g\n", ret, q, c);
  free(p);
  return ret < 0 ? 1 : 0;
}
