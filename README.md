# Installation
Clone into custom nodes directory in ComfyUI:

`git clone https://github.com/Siempreflaco/ComfyUI-NCNodes.git`

**Install dependencies for portable:**

`cd ComfyUI-NCNodes`

`..\..\..\python_embeded\python.exe -m pip install -r requirements.txt`

**Install dependencies for env:**

'cd ComfyUI-NCNodes'

'pip install -r requirements.txt'

---

# Notes
The Image Processor outputs in RGBA mode. When linking to anything that requires RGB mode remove the alpha channel
![Image Processor Node](https://github.com/user-attachments/assets/6b70634c-5505-470f-aae1-a413feb8fe4b)
