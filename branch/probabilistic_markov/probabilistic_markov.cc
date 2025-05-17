#include "probabilistic_markov.h"

bool probabilistic_markov::predict_branch(champsim::address ip)
{
  auto &counter = markov_table[hash(ip)];

  double sum = counter.taken_num + counter.not_taken_num;
  double taken_prob = (sum != 0) ? static_cast<double>(counter.taken_num) / sum : 0.5f;

  return distribution(mt) <= taken_prob;
}

void probabilistic_markov::last_branch_result(champsim::address ip, champsim::address branch_target, bool taken, uint8_t branch_type)
{
  auto &counter = markov_table[hash(ip)];
  if (taken) {
    ++counter.taken_num;
  }
  else {
    ++counter.not_taken_num;
  }
}
