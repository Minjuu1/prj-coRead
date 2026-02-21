"""
Annotation Clustering Service (Phase 2a)

Groups annotations by text proximity within sections.
Rule-based pre-clustering before LLM seed generation.
"""
from difflib import SequenceMatcher


def deduplicate_cross_section(
    annotations_by_agent: dict[str, list],
    section_order: list[str],
) -> dict[str, list]:
    """
    Remove same-agent annotations that repeat similar text across sections.
    Keeps the annotation from the earlier section, drops the later one.
    This catches cases like Conclusion repeating points from Introduction.
    """
    section_idx = {title: i for i, title in enumerate(section_order)}

    deduped = {}
    total_dropped = 0

    for agent_id, annotations in annotations_by_agent.items():
        drop_indices = set()

        for i in range(len(annotations)):
            if i in drop_indices:
                continue
            for j in range(i + 1, len(annotations)):
                if j in drop_indices:
                    continue
                # Only compare across different sections
                if annotations[i].get("sectionTitle") == annotations[j].get("sectionTitle"):
                    continue
                if _texts_overlap(annotations[i]["text"], annotations[j]["text"]):
                    # Drop the one from the later section
                    idx_i = section_idx.get(annotations[i].get("sectionTitle", ""), 999)
                    idx_j = section_idx.get(annotations[j].get("sectionTitle", ""), 999)
                    if idx_i <= idx_j:
                        drop_indices.add(j)
                    else:
                        drop_indices.add(i)
                        break  # i is dropped, stop comparing against it

        deduped[agent_id] = [ann for i, ann in enumerate(annotations) if i not in drop_indices]

        dropped = len(annotations) - len(deduped[agent_id])
        if dropped > 0:
            total_dropped += dropped
            print(f"[Dedup] {agent_id}: dropped {dropped} cross-section duplicate(s)")

    if total_dropped > 0:
        print(f"[Dedup] Total dropped: {total_dropped} cross-section duplicates")

    return deduped


def cluster_annotations(annotations_by_agent: dict[str, list]) -> list[dict]:
    """
    Group annotations into clusters based on section + text proximity.

    Returns list of clusters:
    [
        {
            "clusterId": "cluster_0",
            "sectionTitle": "Introduction",
            "annotations": [ann1, ann2, ...],  # from potentially different agents
            "agents": ["instrumental", "critical"],  # which agents contributed
            "overlapType": "text_overlap" | "same_section_nearby" | "standalone",
        }
    ]
    """
    # Step 1: Flatten all annotations with agent info
    all_annotations = []
    for agent_id, annotations in annotations_by_agent.items():
        for ann in annotations:
            all_annotations.append({
                **ann,
                "agentId": agent_id,
            })

    # Step 2: Group by section
    by_section: dict[str, list] = {}
    for ann in all_annotations:
        section = ann.get("sectionTitle", "Unknown")
        by_section.setdefault(section, []).append(ann)

    # Step 3: Within each section, find text-overlapping clusters
    clusters = []
    cluster_idx = 0

    for section_title, section_anns in by_section.items():
        # Track which annotations have been clustered
        clustered = [False] * len(section_anns)

        # Find text-overlapping pairs
        for i in range(len(section_anns)):
            if clustered[i]:
                continue

            cluster_anns = [section_anns[i]]
            clustered[i] = True

            for j in range(i + 1, len(section_anns)):
                if clustered[j]:
                    continue

                if _texts_overlap(section_anns[i]["text"], section_anns[j]["text"]):
                    cluster_anns.append(section_anns[j])
                    clustered[j] = True

            # Also check transitivity: if A overlaps B and B overlaps C, merge
            # Do another pass to catch indirect overlaps
            changed = True
            while changed:
                changed = False
                for j in range(len(section_anns)):
                    if clustered[j]:
                        continue
                    for existing in cluster_anns:
                        if _texts_overlap(existing["text"], section_anns[j]["text"]):
                            cluster_anns.append(section_anns[j])
                            clustered[j] = True
                            changed = True
                            break

            agents = list(set(a["agentId"] for a in cluster_anns))
            overlap_type = _determine_overlap_type(cluster_anns)

            clusters.append({
                "clusterId": f"cluster_{cluster_idx}",
                "sectionTitle": section_title,
                "annotations": cluster_anns,
                "agents": agents,
                "overlapType": overlap_type,
                "annotationCount": len(cluster_anns),
                "agentCount": len(agents),
            })
            cluster_idx += 1

    # Step 4: Sort clusters by richness (multi-agent first, then by annotation count)
    clusters.sort(key=lambda c: (c["agentCount"], c["annotationCount"]), reverse=True)

    return clusters


def _texts_overlap(text_a: str, text_b: str) -> bool:
    """
    Check if two annotation texts refer to overlapping passages.
    Uses multiple strategies:
    1. Substring containment
    2. Sequence similarity (fuzzy match)
    3. Shared significant phrases
    """
    if not text_a or not text_b:
        return False

    a = text_a.strip()
    b = text_b.strip()

    # Strategy 1: One contains the other
    if a in b or b in a:
        return True

    # Strategy 2: High sequence similarity (>60% overlap)
    ratio = SequenceMatcher(None, a, b).ratio()
    if ratio > 0.6:
        return True

    # Strategy 3: Significant shared substring (30+ chars)
    # Find longest common substring
    match = SequenceMatcher(None, a, b).find_longest_match(0, len(a), 0, len(b))
    if match.size >= 30:
        return True

    return False


def _determine_overlap_type(annotations: list[dict]) -> str:
    """Determine the type of overlap in a cluster."""
    if len(annotations) == 1:
        return "standalone"

    # Check for direct text overlap between any pair
    for i in range(len(annotations)):
        for j in range(i + 1, len(annotations)):
            if _texts_overlap(annotations[i]["text"], annotations[j]["text"]):
                return "text_overlap"

    return "same_section_nearby"


def format_clusters_summary(clusters: list[dict]) -> str:
    """Format clusters for logging/debugging."""
    lines = []
    for c in clusters:
        agents_str = ", ".join(c["agents"])
        lines.append(
            f"  [{c['clusterId']}] {c['sectionTitle']} | "
            f"{c['overlapType']} | {c['agentCount']} agents ({agents_str}) | "
            f"{c['annotationCount']} annotations"
        )
    return "\n".join(lines)
