# A two-minute walkthrough

Open `nvidia-h100-studio.html` in a modern browser. Use the left index to advance manually, or choose **Start guided tour** for the automatic walkthrough. Drag the object to rotate it and use **Take it apart** to separate the layers.

**Opening — The whole picture**

“To understand NVIDIA, start with a product you can take apart. This is an H100 SXM: a documented Hopper-generation example. The question is how its parts, connections, and software work together.”

**Cooling, module, memory, compute**

“The chip needs power and cooling to sustain its performance. The module packages it into something a server can use. High-bandwidth memory feeds the compute die, where many operations happen in parallel. Faster arithmetic helps only if data can reach it. Each layer solves a different bottleneck.”

Select **HBM3 memory**, then **Isolate**, to reveal the five active memory stacks. Return to the index to continue.

**NVLink & NVSwitch**

“Large workloads need multiple GPUs to cooperate. NVLink and NVSwitch connect GPUs within the system. Communication becomes part of the product: individual chip speed alone does not describe the whole machine.”

**CUDA and optimized libraries**

“Now the teardown moves beyond physical parts. CUDA gives developers a shared programming platform. Libraries turn common operations into optimized implementations. Existing code, tools, and developer experience can make adoption easier and switching more work.”

Select **The advantage**, then **The limits**, to make the distinction between capability and interpretation explicit.

**The cluster**

“Networking extends the system across servers. The potential moat comes from making these layers useful together: compute, memory, communication, and software. Its limits matter too. NVIDIA depends on manufacturing and memory partners; competitors offer alternatives, and software can be ported. This is a system to investigate, not a claim of permanent dominance.”

## Presentation facts

- H100 SXM is the baseline here, not NVIDIA's latest GPU.
- This is an original schematic teaching model; component placement is illustrative.
- Hardware specifications and primary evidence appear in each topic. Moat explanations are labeled as inferences.
- The explorer works offline. Opening external source links requires internet access.
