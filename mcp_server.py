import sys
import json
from client import JemallocSlabAllocator

allocator = JemallocSlabAllocator(arena_id=0)

def handle_call(name, arguments):
    if name == "allocate":
        size = arguments.get("size", 32)
        ptr = allocator.allocate(size)
        return {"pointer": ptr, "stats": allocator.stats()}
    elif name == "deallocate":
        ptr = arguments.get("pointer")
        ok = allocator.deallocate(tuple(ptr))
        return {"success": ok, "stats": allocator.stats()}
    elif name == "get_stats":
        return allocator.stats()
    return {"error": f"Unknown tool: {name}"}

def main():
    for line in sys.stdin:
        if not line.strip():
            continue
        try:
            req = json.loads(line)
            res = handle_call(req.get("name"), req.get("arguments", {}))
            print(json.dumps({"id": req.get("id"), "result": res}))
            sys.stdout.flush()
        except Exception as e:
            print(json.dumps({"error": str(e)}))
            sys.stdout.flush()

if __name__ == "__main__":
    main()
