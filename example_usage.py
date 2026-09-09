from client import JemallocSlabAllocator

def main():
    print("=== Testing jemalloc-Style Slab Allocator ===")
    alloc = JemallocSlabAllocator(arena_id=0)

    p1 = alloc.allocate(16)
    print("Allocated small slot (16B):", p1)
    p2 = alloc.allocate(64)
    print("Allocated small slot (64B):", p2)
    p3 = alloc.allocate(8192)
    print("Allocated large page chunk (8192B):", p3)

    st = alloc.stats()
    print("Allocator statistics:", st)
    assert st["slabs_active"] >= 2
    assert st["large_count"] == 1

    ok1 = alloc.deallocate(p1)
    ok3 = alloc.deallocate(p3)
    assert ok1 and ok3
    print("Successfully deallocated p1 and p3. Final stats:", alloc.stats())
    print("=== All tests passed successfully! ===")

if __name__ == "__main__":
    main()
