#include "pseudo_lru.h"

#include <algorithm>
#include <cassert>

pseudo_lru::bits_tree::bits_tree(long ways)
{
  for (size_t nodes_num = 1; ways > 1; ways /= 2, nodes_num *= 2) {
    level lvl {nodes_num, NodeBit::LEFT};
    tree.emplace_back(std::move(lvl));
  }
}

long pseudo_lru::bits_tree::find_victim()
{
    long idx = 0;

    for (auto &lvl: tree) {
        idx = idx * 2 + (lvl[idx] != NodeBit::LEFT);
    }

    return idx;
}

void pseudo_lru::bits_tree::update_way(long way)
{
    long idx = way / 2;

    for (auto level_rit = tree.rbegin(); level_rit != tree.rend(); ++level_rit) {
        auto &node = (*level_rit)[idx];
        node = static_cast<NodeBit>(node ^ 1); // invert bit
        idx = idx / 2;
    }
}

pseudo_lru::pseudo_lru(CACHE* cache) : pseudo_lru(cache, cache->NUM_SET, cache->NUM_WAY) {}

pseudo_lru::pseudo_lru(CACHE* cache, long sets, long ways) : replacement(cache), trees(sets, pseudo_lru::bits_tree(ways)) {}

long pseudo_lru::find_victim(uint32_t triggering_cpu, uint64_t instr_id, long set, const champsim::cache_block* current_set, champsim::address ip,
                      champsim::address full_addr, access_type type)
{
    return trees.at(static_cast<std::size_t>(set)).find_victim();
}

void pseudo_lru::replacement_cache_fill(uint32_t triggering_cpu, long set, long way, champsim::address full_addr, champsim::address ip, champsim::address victim_addr,
                                 access_type type)
{
  trees.at(static_cast<std::size_t>(set)).update_way(way);
}

void pseudo_lru::update_replacement_state(uint32_t triggering_cpu, long set, long way, champsim::address full_addr, champsim::address ip,
                                   champsim::address victim_addr, access_type type, uint8_t hit)
{
  if (hit && access_type{type} != access_type::WRITE)
    trees.at(static_cast<std::size_t>(set)).update_way(way);
}
