---
title: Tab variations
---

## Text tabs

::::{tab-set}
:::{tab-item} Python
Python tab body.
:::

:::{tab-item} TypeScript
TypeScript tab body.
:::
::::

## Special characters

::::{tab-set}
:::{tab-item} a > b "best"
Tab body with special title characters.
:::
::::

## Mixed content tabs

::::{tab-set}
:::{tab-item} Overview
Plain paragraph in one tab.
:::

:::{tab-item} Example
```python
print("code in a non-codegroup tab")
```
:::
::::

## Inline tabs

````{tab} Async
```python
await add(1, 2)
```
````

````{tab} Sync
```python
add(1, 2)
```
````

## Separate inline tab group

````{tab} HTTP
```bash
curl -X GET /
```
````

````{tab} gRPC
```python
client.fetch()
```
````

## Inline tab new-set

````{tab} First
```python
one()
```
````

````{tab} Second
:new-set:
```python
two()
```
````

````{tab} Third
```python
three()
```
````
