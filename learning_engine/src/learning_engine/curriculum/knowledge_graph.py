"""Knowledge Graph and Prerequisite Engine (Feature Set D).

Provides:
- Built-in concept dependency graphs for Computer Science, Networking, Cybersecurity,
  Programming/DSA, Operating Systems, Databases, Machine Learning, and Web Development.
- Prerequisite chain resolution & missing-foundation detection.
- Next-logical-topic recommender based on already mastered/known concepts.
- Mermaid diagram generator (`flowchart TD` / `flowchart LR`) for visual concept maps.
"""

from __future__ import annotations

from typing import Any
from ..core.models import ConceptNode

BUILTIN_CONCEPT_NODES: list[ConceptNode] = [
    # Computer Science Core
    ConceptNode("cs-binary", "Binary & Number Systems", "computer_science", "beginner", [], ["net-binary", "cs-arch"], "Bits, bytes, binary/hex representation, and two's complement."),
    ConceptNode("cs-prog-basics", "Programming Fundamentals", "computer_science", "beginner", ["cs-binary"], ["dsa-arrays", "c-pointers", "py-basics"], "Variables, control flow, functions, and basic I/O."),
    ConceptNode("cs-math", "Discrete Mathematics", "computer_science", "beginner", [], ["dsa-trees", "dsa-graphs", "db-relational", "sec-crypto"], "Logic, sets, combinatorics, graph theory, and modular arithmetic."),
    ConceptNode("cs-arch", "Computer Architecture", "computer_science", "intermediate", ["cs-binary", "cs-prog-basics"], ["os-processes", "os-memory"], "CPU pipeline, registers, caches, memory hierarchy, and ISA."),
    # C & Data Structures (DSA)
    ConceptNode("c-pointers", "Pointers & Memory Layout in C", "dsa", "beginner", ["cs-prog-basics"], ["dsa-linked-list", "dsa-trees", "os-memory"], "Stack vs heap, address-of (&), dereference (*), pointer arithmetic, and malloc/free."),
    ConceptNode("dsa-arrays", "Arrays, Strings & Complexity (Big-O)", "dsa", "beginner", ["cs-prog-basics"], ["dsa-sorting", "dsa-linked-list", "dsa-hash"], "Contiguous memory allocation, asymptotic time/space analysis, and two-pointer patterns."),
    ConceptNode("dsa-linked-list", "Singly & Doubly Linked Lists", "dsa", "intermediate", ["c-pointers", "dsa-arrays"], ["dsa-stacks-queues", "dsa-trees"], "Dynamic node allocation, struct self-reference, insertion, deletion, and cycle detection."),
    ConceptNode("dsa-stacks-queues", "Stacks, Queues & Monotonic Deques", "dsa", "intermediate", ["dsa-linked-list"], ["dsa-trees", "dsa-graphs"], "LIFO/FIFO abstractions, call-stack frames, and ring buffers."),
    ConceptNode("dsa-hash", "Hash Tables & Collision Resolution", "dsa", "intermediate", ["dsa-arrays"], ["db-indexing"], "Hash functions, chaining vs open addressing, load factor, and amortized O(1) lookup."),
    ConceptNode("dsa-trees", "Trees, Binary Search Trees & Heaps", "dsa", "intermediate", ["dsa-linked-list", "cs-math"], ["dsa-graphs", "db-indexing"], "Tree traversals (DFS/BFS), BST invariants, balanced trees (AVL/B-Tree), and priority queues."),
    ConceptNode("dsa-sorting", "Sorting & Divide-and-Conquer", "dsa", "intermediate", ["dsa-arrays"], ["dsa-dp"], "Merge sort, quicksort, heap sort, stability, and recurrence relations."),
    ConceptNode("dsa-graphs", "Graph Algorithms (BFS, DFS, Dijkstra, MST)", "dsa", "advanced", ["dsa-trees", "dsa-stacks-queues"], ["net-routing", "dsa-dp"], "Adjacency lists, shortest paths, topological sort, and spanning trees."),
    ConceptNode("dsa-dp", "Dynamic Programming & Greedy Algorithms", "dsa", "advanced", ["dsa-sorting", "dsa-graphs"], [], "Optimal substructure, overlapping subproblems, memoization, and tabulation."),
    # Networking
    ConceptNode("net-binary", "Binary Basics & Octets", "networking", "beginner", ["cs-binary"], ["net-ip"], "8-bit octets, dotted-decimal notation, and bitwise AND/OR operations."),
    ConceptNode("net-osi", "OSI & TCP/IP Layer Models", "networking", "beginner", [], ["net-ip", "net-tcp-udp"], "Encapsulation: Physical, Data Link (MAC), Network (IP), Transport (TCP/UDP), and Application layers."),
    ConceptNode("net-ip", "IPv4/IPv6 Addressing", "networking", "beginner", ["net-binary", "net-osi"], ["net-subnetting", "net-routing"], "Network ID vs Host ID, private ranges (RFC 1918), NAT, and loopback."),
    ConceptNode("net-subnetting", "Subnetting, CIDR & VLSM", "networking", "intermediate", ["net-ip"], ["net-routing", "net-security"], "Prefix lengths (/24, /26), subnet masks, broadcast calculation, and variable-length subnet masking."),
    ConceptNode("net-tcp-udp", "TCP/IP Transport, Handshake & Congestion Control", "networking", "intermediate", ["net-osi", "net-ip"], ["net-dns", "net-http", "net-security"], "3-way handshake (SYN, SYN-ACK, ACK), flow control, retransmissions, and UDP datagrams."),
    ConceptNode("net-dns", "DNS Resolution & Hierarchy", "networking", "intermediate", ["net-tcp-udp"], ["net-http", "net-security"], "Recursive resolvers, root/TLD/authoritative nameservers, A/AAAA/CNAME/MX records, and caching TTL."),
    ConceptNode("net-routing", "Switching, VLANs & Routing Protocols (OSPF/BGP)", "networking", "advanced", ["net-subnetting", "dsa-graphs"], ["net-security"], "Forwarding tables, longest-prefix match, autonomous systems, and interior/exterior gateway routing."),
    ConceptNode("net-http", "HTTP/1.1, HTTP/2, HTTP/3 & TLS", "networking", "intermediate", ["net-dns", "net-tcp-udp"], ["web-backend", "net-security"], "Request/response semantics, headers, status codes, TLS handshake, and multiplexing."),
    ConceptNode("net-security", "Network Security, Firewalls & IDS/IPS", "networking", "advanced", ["net-subnetting", "net-tcp-udp", "net-dns"], ["sec-web"], "Packet filtering, stateful inspection, zero-trust segmentation, TLS/mTLS, and anomaly detection."),
    # Operating Systems
    ConceptNode("os-processes", "Processes, Threads & Context Switching", "operating_systems", "beginner", ["cs-arch"], ["os-scheduling", "os-sync"], "PCB, user vs kernel mode, system calls, fork/exec, and thread concurrency."),
    ConceptNode("os-scheduling", "CPU Scheduling Algorithms", "operating_systems", "intermediate", ["os-processes"], ["os-sync"], "FCFS, SJF/SRTF, Round Robin, Multi-Level Feedback Queue, turnaround vs response time."),
    ConceptNode("os-sync", "Concurrency, Mutexes, Semaphores & Deadlocks", "operating_systems", "intermediate", ["os-processes"], ["db-transactions"], "Race conditions, critical sections, Coffman deadlock conditions, and Banker's algorithm."),
    ConceptNode("os-memory", "Virtual Memory, Paging & Page Replacement", "operating_systems", "intermediate", ["cs-arch", "c-pointers"], ["os-filesystems"], "Page tables, TLB, page faults, thrashing, and LRU/Clock replacement policies."),
    ConceptNode("os-filesystems", "File Systems, Inodes & Disk I/O", "operating_systems", "advanced", ["os-memory"], [], "Inodes, directory trees, journaling, crash consistency, and VFS abstraction."),
    # Databases
    ConceptNode("db-relational", "Relational Model & SQL Foundations", "databases", "beginner", ["cs-math"], ["db-normalization", "db-indexing"], "Tables, primary/foreign keys, relational algebra, SELECT/JOIN/GROUP BY."),
    ConceptNode("db-normalization", "Schema Design & Normalization (1NF-BCNF)", "databases", "intermediate", ["db-relational"], ["db-transactions", "web-django-orm"], "Functional dependencies, lossless-join decomposition, and anomaly elimination."),
    ConceptNode("db-indexing", "B+ Tree & Hash Indexing, Query Plans", "databases", "intermediate", ["db-relational", "dsa-trees", "dsa-hash"], ["db-transactions"], "Clustered vs unclustered indexes, composite key ordering, and EXPLAIN query execution."),
    ConceptNode("db-transactions", "ACID Transactions, Isolation Levels & MVCC", "databases", "advanced", ["db-normalization", "os-sync"], [], "Atomicity, write-ahead logging (WAL), two-phase locking (2PL), dirty/phantom reads, and MVCC."),
    # Python & Web / Django
    ConceptNode("py-basics", "Python Syntax, Data Types & Control Flow", "python", "beginner", ["cs-prog-basics"], ["py-oop", "py-stdlib"], "Lists, dicts, sets, comprehensions, functions, and exception handling."),
    ConceptNode("py-oop", "Python Object-Oriented & Functional Patterns", "python", "intermediate", ["py-basics"], ["web-backend", "web-django-orm"], "Classes, dataclasses, dunder methods, iterators, generators, and decorators."),
    ConceptNode("py-stdlib", "Modules, Virtual Environments & Testing", "python", "intermediate", ["py-basics"], ["web-backend"], "Packaging, pathlib, unittest/pytest, and type annotations."),
    ConceptNode("web-backend", "Web Architecture, Routing & REST APIs", "web_dev", "intermediate", ["net-http", "py-oop"], ["web-django-orm", "sec-web"], "MVC/MTV pattern, request-response lifecycle, middleware, and authentication."),
    ConceptNode("web-django-orm", "Django Models, ORM, Views, Templates & Auth", "web_dev", "intermediate", ["web-backend", "db-normalization"], ["sec-web"], "Migrations, QuerySets, forms, CSRF protection, and test client."),
    # Cybersecurity (Defensive)
    ConceptNode("sec-crypto", "Applied Cryptography & Hashing", "cybersecurity", "intermediate", ["cs-math"], ["net-security", "sec-web"], "Symmetric (AES-GCM), asymmetric (RSA/ECC), SHA-256, HMAC, and password hashing (Argon2/bcrypt)."),
    ConceptNode("sec-web", "Defensive Web Security (OWASP Top 10 Remediation)", "cybersecurity", "intermediate", ["net-http", "web-backend", "db-relational"], [], "Parameterized queries against SQLi, context-aware output encoding against XSS, CSRF tokens, and RBAC."),
]


class KnowledgeGraph:
    """Manages concept nodes, prerequisite resolution, and visual concept maps."""

    def __init__(self, extra_nodes: list[ConceptNode] | None = None) -> None:
        self.nodes: dict[str, ConceptNode] = {n.concept_id: n for n in BUILTIN_CONCEPT_NODES}
        for n in extra_nodes or []:
            self.nodes[n.concept_id] = n

    def add_node(self, node: ConceptNode) -> None:
        self.nodes[node.concept_id] = node

    def get_domain_nodes(self, domain_or_query: str) -> list[ConceptNode]:
        q = domain_or_query.lower()
        domain_map = {
            "network": "networking",
            "subnet": "networking",
            "tcp": "networking",
            "dns": "networking",
            "operating system": "operating_systems",
            "os ": "operating_systems",
            "deadlock": "operating_systems",
            "database": "databases",
            "sql": "databases",
            "dsa": "dsa",
            "data structure": "dsa",
            "algorithm": "dsa",
            "c programming": "dsa",
            "pointer": "dsa",
            "python": "python",
            "django": "web_dev",
            "web": "web_dev",
            "cybersecurity": "cybersecurity",
            "security": "cybersecurity",
        }
        matched_domain = None
        for kw, dom in domain_map.items():
            if kw in q:
                matched_domain = dom
                break
        if matched_domain:
            return [n for n in self.nodes.values() if n.domain == matched_domain]
        # Fallback keyword search across titles/summaries
        found = [n for n in self.nodes.values() if q in n.title.lower() or q in n.summary.lower() or q in n.domain.lower()]
        return found or list(self.nodes.values())[:8]

    def get_prerequisites_chain(self, concept_id: str) -> list[ConceptNode]:
        """Return topologically ordered prerequisite ConceptNodes required before `concept_id`."""
        visited: set[str] = set()
        order: list[ConceptNode] = []

        def dfs(cid: str) -> None:
            if cid in visited or cid not in self.nodes:
                return
            visited.add(cid)
            node = self.nodes[cid]
            for pre in node.prerequisites:
                dfs(pre)
            if cid != concept_id:
                order.append(node)

        dfs(concept_id)
        return order

    def detect_missing_foundations(self, target_concept_id: str, known_concepts: set[str] | list[str]) -> list[ConceptNode]:
        """Return prerequisite concepts for `target_concept_id` that the learner has not yet covered."""
        known = set(known_concepts)
        chain = self.get_prerequisites_chain(target_concept_id)
        return [n for n in chain if n.concept_id not in known]

    def recommend_next_topics(self, known_concepts: set[str] | list[str], domain: str | None = None) -> list[ConceptNode]:
        """Recommend concepts whose prerequisites are all satisfied by `known_concepts`."""
        known = set(known_concepts)
        candidates: list[ConceptNode] = []
        for node in self.nodes.values():
            if node.concept_id in known:
                continue
            if domain and node.domain != domain:
                continue
            if all(p in known for p in node.prerequisites):
                candidates.append(node)
        return candidates

    def to_mermaid_flowchart(self, concept_ids: list[str] | None = None, mastered: set[str] | None = None) -> str:
        """Render a valid Mermaid `flowchart TD` showing prerequisite dependencies."""
        mastered_set = set(mastered or set())
        selected = [self.nodes[cid] for cid in concept_ids if cid in self.nodes] if concept_ids else list(self.nodes.values())[:12]
        selected_ids = {n.concept_id for n in selected}
        # Include immediate prerequisites so edges are connected
        for n in list(selected):
            for p in n.prerequisites:
                if p in self.nodes and p not in selected_ids:
                    selected.append(self.nodes[p])
                    selected_ids.add(p)

        lines = ["flowchart TD"]
        for n in selected:
            safe_id = n.concept_id.replace("-", "_")
            status = " [Mastered]" if n.concept_id in mastered_set else ""
            label = f'{n.title}{status}'.replace('"', "'")
            lines.append(f'    {safe_id}["{label}"]')
        for n in selected:
            target_id = n.concept_id.replace("-", "_")
            for p in n.prerequisites:
                if p in selected_ids:
                    src_id = p.replace("-", "_")
                    lines.append(f"    {src_id} --> {target_id}")
        return "\n".join(lines)
