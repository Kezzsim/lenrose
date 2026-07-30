"""Introspect a Tiled server: enumerate containers and discover metadata keys."""

from __future__ import annotations

from dataclasses import dataclass, field


def flatten(metadata: dict, prefix: str = "") -> dict[str, object]:
    """Flatten nested metadata into dotted keys.

    Lists of scalars are kept as-is; lists of dicts and nested dicts are
    recursed with dotted paths.
    """
    out: dict[str, object] = {}
    for key, value in metadata.items():
        dotted = f"{prefix}.{key}" if prefix else str(key)
        if isinstance(value, dict):
            out.update(flatten(value, dotted))
        else:
            out[dotted] = value
    return out


def infer_type(value: object) -> str:
    """Infer a Typesense field type from a Python value."""
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, int):
        return "int64"
    if isinstance(value, float):
        return "float"
    if isinstance(value, str):
        return "string"
    if isinstance(value, (list, tuple)):
        if not value:
            return "string[]"
        elem = value[0]
        if isinstance(elem, bool):
            return "bool[]"
        if isinstance(elem, int):
            return "int64[]"
        if isinstance(elem, float):
            return "float[]"
        return "string[]"
    # dicts should have been flattened; fall back to string
    return "string"


# Ordering used when reconciling conflicting types across records: prefer the
# more general type. string is the universal fallback.
_TYPE_RANK = {
    "bool": 0,
    "int64": 1,
    "float": 2,
    "string": 3,
    "bool[]": 0,
    "int64[]": 1,
    "float[]": 2,
    "string[]": 3,
}


def _reconcile(existing: str, new: str) -> str:
    if existing == new:
        return existing
    existing_arr = existing.endswith("[]")
    new_arr = new.endswith("[]")
    # If one is array and the other scalar, promote to string to be safe.
    if existing_arr != new_arr:
        return "string[]" if (existing_arr or new_arr) else "string"
    # Same arrayness: pick the higher-ranked (more general) type.
    return existing if _TYPE_RANK[existing] >= _TYPE_RANK[new] else new


@dataclass
class DiscoveredKey:
    dotted_key: str
    datatype: str
    sample: object = None


@dataclass
class ContainerInfo:
    path: str
    count: int | None = None


@dataclass
class IntrospectionResult:
    keys: dict[str, DiscoveredKey] = field(default_factory=dict)
    scanned: int = 0

    def as_key_list(self) -> list[DiscoveredKey]:
        return sorted(self.keys.values(), key=lambda k: k.dotted_key)


#: Sentinel path used to reference the root container itself (a Tiled tree
#: whose immediate children are records rather than nested containers).
ROOT_PATH = ""


def _family_name(node) -> str | None:
    """Return the structure family of a node as a plain string.

    Tiled exposes ``structure_family`` as a ``StructureFamily`` enum whose
    ``str()`` is ``"StructureFamily.container"`` while its ``.value`` is
    ``"container"``. Fakes may set it to a plain string. Normalise both here.
    """
    family = getattr(node, "structure_family", None)
    if family is None:
        return None
    # Enum instances carry a ``value`` attribute with the canonical string.
    value = getattr(family, "value", None)
    if isinstance(value, str):
        return value
    return str(family)


def _is_container(node) -> bool:
    """Whether ``node`` is (or is treated as) a container of children."""
    family = _family_name(node)
    # ``None`` means the node did not advertise a family; treat it as a
    # container so we do not silently drop entries.
    return family is None or family == "container"


def list_containers(client) -> list[ContainerInfo]:
    """List top-level container entries available to the user.

    Only children that are themselves containers are returned. If the root
    tree holds records directly (no nested containers), the result is empty;
    callers should fall back to :data:`ROOT_PATH` via
    :func:`has_nested_containers`.
    """
    infos: list[ContainerInfo] = []
    for key in client.keys():
        child = client[key]
        if _is_container(child):
            try:
                count = len(child)
            except Exception:
                count = None
            infos.append(ContainerInfo(path=str(key), count=count))
    return infos


def has_nested_containers(client) -> bool:
    """Return True if the root tree exposes at least one nested container.

    When this is False, all records live directly in the root container and
    the UI should go straight to key selection using :data:`ROOT_PATH`.
    """
    for key in client.keys():
        if _is_container(client[key]):
            return True
    return False


def introspect_container(
    client, container_path: str = ROOT_PATH, limit: int = 100
) -> IntrospectionResult:
    """Walk up to ``limit`` records in a container and discover metadata keys.

    ``container_path`` may be :data:`ROOT_PATH` (the empty string) to
    introspect the records held directly in the root tree, for servers where
    all data lives in the root container without any nesting.
    """
    result = IntrospectionResult()
    container = client if container_path == ROOT_PATH else client[container_path]

    for _, node in container.items()[:limit]:
        metadata = dict(node.metadata or {})
        flat = flatten(metadata)
        for dotted, value in flat.items():
            dtype = infer_type(value)
            if dotted in result.keys:
                merged = _reconcile(result.keys[dotted].datatype, dtype)
                result.keys[dotted].datatype = merged
            else:
                result.keys[dotted] = DiscoveredKey(dotted, dtype, sample=value)
        result.scanned += 1

    return result
