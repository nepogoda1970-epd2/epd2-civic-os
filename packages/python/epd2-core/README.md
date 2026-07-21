# epd2-core

Единственный Python-пакет, который на этапе CLAUDE-PACK-01 содержит
исполняемый код. Не содержит бизнес-логики.

## Содержимое

- `epd2_core.version` — константы `CANON_VERSION` и `REPOSITORY_VERSION`.
- `epd2_core.identifiers` — минимальные утилиты для работы с каноническими
  идентификаторами: `generate_uuid()` и `is_valid_uuid()`.

## Использование

```python
from epd2_core.version import CANON_VERSION, REPOSITORY_VERSION
from epd2_core.identifiers import generate_uuid, is_valid_uuid

new_id = generate_uuid()
assert is_valid_uuid(str(new_id))
```

## Границы

Этот пакет не должен получать доменные сущности, доменные статусы или
бизнес-правила конкретного контура. Он используется как общая
инфраструктурная зависимость будущих сервисов.
