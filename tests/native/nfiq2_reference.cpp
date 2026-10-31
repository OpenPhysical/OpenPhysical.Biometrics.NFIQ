// Calls the upstream C++ API directly, separately from the C/.NET wrapper.
#include <cstdlib>
#include <fstream>
#include <iostream>
#include <nfiq2.hpp>
#include <vector>
int main(int argc, char **argv) {
  if (argc != 2 && argc != 4)
    return 2;
  std::ifstream f(argv[1], std::ios::binary);
  std::vector<uint8_t> b((std::istreambuf_iterator<char>(f)), {});
  const auto width = argc == 4 ? std::atoi(argv[2]) : 512;
  const auto height = argc == 4 ? std::atoi(argv[3]) : 512;
  if (width <= 0 || height <= 0 ||
      b.size() != static_cast<size_t>(width) * height)
    return 3;
  try {
    NFIQ2::Algorithm algorithm;
    NFIQ2::FingerprintImageData image(b.data(), b.size(), width, height, 0,
                                      500);
    const auto score = algorithm.computeUnifiedQualityScore(image);
    std::cout << "0 " << score << " 0 " << algorithm.getParameterHash()
              << std::endl;
  } catch (const NFIQ2::Exception &error) {
    std::cout << "3 0 " << static_cast<int>(error.getErrorCode()) << std::endl;
  }
}
