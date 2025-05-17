#include "markov.h"

bool markov::predict_branch(champsim::address ip) {
  auto &counter = markov_table[hash(ip)];
  return counter.taken_num > counter.not_taken_num;
}

void markov::last_branch_result(champsim::address ip, champsim::address branch_target, bool taken, uint8_t branch_type) {
  auto &counter = markov_table[hash(ip)];
  if (taken) {
    ++counter.taken_num;
  }
  else {
    ++counter.not_taken_num;
  }
}
