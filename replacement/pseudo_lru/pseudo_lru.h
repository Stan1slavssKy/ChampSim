#ifndef REPLACEMENT_PSEUDO_LRU_H
#define REPLACEMENT_PSEUDO_LRU_H

#include <vector>

#include "cache.h"
#include "modules.h"

class pseudo_lru : public champsim::modules::replacement
{
    enum NodeBit: uint8_t {
        LEFT = 0,
        RIGTH = 1,
    };

    class bits_tree final {
        // each level in the tree consists of nodes * 2 in comparison to previous tree level.
        using level = std::vector<NodeBit>;
        std::vector<level> tree;

    public:
        bits_tree(long ways);
        
        long find_victim();
        void update_way(long way);
    };

    std::vector<bits_tree> trees;

public:
  explicit pseudo_lru(CACHE* cache);
  pseudo_lru(CACHE* cache, long sets, long ways);

  // void initialize_replacement();
  long find_victim(uint32_t triggering_cpu, uint64_t instr_id, long set, const champsim::cache_block* current_set, champsim::address ip,
                   champsim::address full_addr, access_type type);
  void replacement_cache_fill(uint32_t triggering_cpu, long set, long way, champsim::address full_addr, champsim::address ip, champsim::address victim_addr,
                              access_type type);
  void update_replacement_state(uint32_t triggering_cpu, long set, long way, champsim::address full_addr, champsim::address ip, champsim::address victim_addr,
                                access_type type, uint8_t hit);
  // void replacement_final_stats()
};

#endif // REPLACEMENT_PSEUDO_LRU_H
