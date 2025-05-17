#ifndef PROBABILISTIC_MARKOV_MARKOV_H
#define PROBABILISTIC_MARKOV_MARKOV_H

#include <array>
#include <random>

#include "address.h"
#include "modules.h"

class probabilistic_markov : champsim::modules::branch_predictor
{
  [[nodiscard]] static constexpr auto hash(champsim::address ip) { return ip.to<unsigned long>() % PRIME; }

  static constexpr std::size_t TABLE_SIZE = 16384;
  static constexpr std::size_t PRIME = 16381;

  struct freqs_counter {
    uint32_t taken_num {0};
    uint32_t not_taken_num {0};
  };
  
  std::array<freqs_counter, TABLE_SIZE> markov_table;

  std::mt19937 mt;
  std::uniform_real_distribution<> distribution{0.0, 1.0};

public:
  using branch_predictor::branch_predictor;

  bool predict_branch(champsim::address ip);
  void last_branch_result(champsim::address ip, champsim::address branch_target, bool taken, uint8_t branch_type);
};

#endif // PROBABILISTIC_MARKOV_MARKOV_H
