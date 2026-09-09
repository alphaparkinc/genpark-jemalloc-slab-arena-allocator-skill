class JemallocSlabAllocator:
    """
    Slab allocator model inspired by jemalloc.
    Size classes: 16, 32, 64, 128, 256, 512, 1024, 2048 bytes.
    Each Slab manages a 4096-byte chunk partitioned into fixed-size slots with bitmap tracking.
    Arenas partition allocation pools to eliminate thread lock contention.
    """
    SIZE_CLASSES = [16, 32, 64, 128, 256, 512, 1024, 2048]
    PAGE_SIZE = 4096

    def __init__(self, arena_id=0):
        self.arena_id = arena_id
        self.slabs = {sc: [] for sc in self.SIZE_CLASSES}
        self.allocated_bytes = 0
        self.large_allocations = {}

    def _pick_size_class(self, size):
        for sc in self.SIZE_CLASSES:
            if size <= sc:
                return sc
        return None

    def allocate(self, size):
        if size <= 0:
            raise ValueError("Allocation size must be positive")
        sc = self._pick_size_class(size)
        if sc is not None:
            for slab in self.slabs[sc]:
                idx = slab.alloc_slot()
                if idx is not None:
                    self.allocated_bytes += sc
                    return (slab.slab_id, sc, idx)
            new_slab = Slab(len(self.slabs[sc]) + 1000 * sc, sc, self.PAGE_SIZE)
            idx = new_slab.alloc_slot()
            self.slabs[sc].append(new_slab)
            self.allocated_bytes += sc
            return (new_slab.slab_id, sc, idx)
        else:
            pages = (size + self.PAGE_SIZE - 1) // self.PAGE_SIZE
            alloc_id = f"large_{len(self.large_allocations) + 1}"
            alloc_sz = pages * self.PAGE_SIZE
            self.large_allocations[alloc_id] = alloc_sz
            self.allocated_bytes += alloc_sz
            return (alloc_id, alloc_sz, 0)

    def deallocate(self, ptr):
        tag, sc_or_sz, idx = ptr
        if isinstance(tag, str) and tag.startswith("large_"):
            sz = self.large_allocations.pop(tag, 0)
            self.allocated_bytes -= sz
            return True
        else:
            sc = sc_or_sz
            for slab in self.slabs.get(sc, []):
                if slab.slab_id == tag:
                    if slab.free_slot(idx):
                        self.allocated_bytes -= sc
                        return True
        return False

    def stats(self):
        return {
            "arena_id": self.arena_id,
            "allocated_bytes": self.allocated_bytes,
            "slabs_active": sum(len(s) for s in self.slabs.values()),
            "large_count": len(self.large_allocations)
        }

class Slab:
    def __init__(self, slab_id, slot_size, page_size=4096):
        self.slab_id = slab_id
        self.slot_size = slot_size
        self.total_slots = page_size // slot_size
        self.free_slots = set(range(self.total_slots))

    def alloc_slot(self):
        if not self.free_slots:
            return None
        return self.free_slots.pop()

    def free_slot(self, idx):
        if 0 <= idx < self.total_slots and idx not in self.free_slots:
            self.free_slots.add(idx)
            return True
        return False
