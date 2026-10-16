---
title: Soil is often part of the plant model; judge planters by render, not by name search
topic: placement-layout-design
tags: [soil, planter, name search, substring, audit, dressing]
summary: A search for '*soil*' renderers flags pots whose soil is baked into the plant mesh and atlas; filter geometrically and look at every survivor before building anything.
---
**Symptom:** An audit for "planters missing soil" (renderer named `*soil*`/`*mulch*` or using a soil material) flags 19 hosts; after inspection zero needed anything. Soil discs built into two of them were proven redundant by an A/B render and deleted.

**Cause:** Many plant models ship pot, soil surface and foliage as **one mesh with one atlas**. A renderer named `*Planter*` can be the whole plant (bounds from base to leaf tip), so a "does a plant sit above this pot?" test finds nothing. Substring matching adds junk: "spot" contains "pot", and `bed`/`urn`/`sleeve` filters matched walls, glazing and light strips (175 bogus hits).

**Fix / rule:** Filter geometrically (a plant renderer with a container directly beneath it), then render every survivor from just above its rim before building anything. Do not build off a name list.
