import torch
import torchvision.transforms.v2 as T
from PIL import Image
from transparent_background import Remover
from comfy.utils import ProgressBar

class NCImageProcessor:
    def __init__(self):
        pass
    
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "image": ("IMAGE",),
                "mode": (["base", "fast", "base-nightly"],),
                "use_jit": ("BOOLEAN", {"default": True}),
                "resolution": ("INT", {
                    "default": 1024, 
                    "min": 64, 
                    "max": 4096, 
                    "step": 1,
                    "display": "number"
                }),
                "border": ("INT", {
                    "default": 64, 
                    "min": 0, 
                    "max": 1024, 
                    "step": 1,
                    "display": "number"
                }),
                "crop": ("BOOLEAN", {"default": True}),
            },
            "optional": {
                "background": (["Alpha", "black", "white", "gray", "green", "blue", "red"], {"default": "Alpha", "tooltip": "Choose background color"})
            }
        }

    RETURN_TYPES = ("IMAGE", "MASK",)
    RETURN_NAMES = ("IMAGE", "MASK",)

    FUNCTION = "execute"
    CATEGORY = "NCNodes/ImageProcessing"
    
    def execute(self, image, mode, use_jit, resolution=1024, border=64, crop=True, background="Alpha"):
        background_colors = {
            "Alpha": (0, 0, 0, 0),
            "black": (0, 0, 0, 255),
            "white": (255, 255, 255, 255),
            "gray": (128, 128, 128, 255),
            "green": (0, 255, 0, 255),
            "blue": (0, 0, 255, 255),
            "red": (255, 0, 0, 255),
        }

        # Initialize progress bar
        total_steps = image.shape[0] * 4 # 4 main steps per image
        progress_bar = ProgressBar(total_steps)

        bg_color = background_colors.get(background, (0, 0, 0, 0))
        target_size = resolution - (border * 2)

        session = Remover(mode=mode, jit=use_jit)

        image = image.permute([0, 3, 1, 2])
        output = []
        masks = []

        for img_idx, img in enumerate(image):
            img = T.ToPILImage()(img)

            # Step 1: Process to remove background
            img = session.process(img)
            progress_bar.update_absolute(img_idx * 4 + 1)

            if img.mode != 'RGBA':
                img = img.convert('RGBA')

            # Step 2: Store alpha mask
            alpha_mask = img.split()[-1]
            masks.append(T.ToTensor()(alpha_mask))
            output.append(T.ToTensor()(img))
            progress_bar.update_absolute(img_idx * 4 + 2)

        output = torch.stack(output, dim=0).permute([0, 2, 3, 1])  # (N,H,W,C)
        masks = torch.stack(masks, dim=0).permute([0, 2, 3, 1]).squeeze(-1)  # (N,H,W)

        final_images = []
        final_masks = []

        for i in range(output.shape[0]):
            current_image = output[i]
            current_mask = masks[i]

            if crop:
                # Step 3: Crop if enabled
                mask_non_zero = current_mask > 0.5
                non_zero_coords = torch.nonzero(mask_non_zero)
                
                if len(non_zero_coords) > 0:
                    min_y, min_x = non_zero_coords.min(dim=0)[0]
                    max_y, max_x = non_zero_coords.max(dim=0)[0]
                    current_image = current_image[min_y:max_y+1, min_x:max_x+1, :]
                    current_mask = current_mask[min_y:max_y+1, min_x:max_x+1]

            progress_bar.update_absolute(i * 4 + 3)

            # Apply background color (if not Alpha)
            if background != "Alpha":
                current_pil = T.ToPILImage()(current_image.permute(2, 0, 1))
                bg_img = Image.new('RGBA', current_pil.size, bg_color)
                bg_img.paste(current_pil, (0, 0), current_pil)
                current_image = T.ToTensor()(bg_img).permute(1, 2, 0)

            # Pad to square (1:1) based on current dimensions
            h, w = current_image.shape[:2]
            max_size = max(h, w)
            pad_h = (max_size - h) // 2
            pad_w = (max_size - w) // 2
            
            padded_image = torch.zeros((max_size, max_size, 4)) if background == "Alpha" else torch.ones((max_size, max_size, 4))
            if background != "Alpha":
                padded_image[:, :] = torch.tensor([c/255 for c in bg_color])
            padded_image[pad_h:pad_h+h, pad_w:pad_w+w] = current_image
            
            padded_mask = torch.zeros((max_size, max_size))
            padded_mask[pad_h:pad_h+h, pad_w:pad_w+w] = current_mask

            # Resize to target_size (resolution - border*2)
            resized_pil = T.ToPILImage()(padded_image.permute(2, 0, 1)).resize((target_size, target_size), Image.LANCZOS)
            resized_mask_pil = Image.fromarray((padded_mask.numpy() * 255).astype('uint8')).resize((target_size, target_size), Image.LANCZOS)

            resized_image = T.ToTensor()(resized_pil).permute(1, 2, 0)
            resized_mask = T.ToTensor()(resized_mask_pil).squeeze(0)

            # Add border to reach final resolution
            final_image = torch.zeros((resolution, resolution, 4)) if background == "Alpha" else torch.ones((resolution, resolution, 4))
            if background != "Alpha":
                final_image[:, :] = torch.tensor([c/255 for c in bg_color])
            
            final_mask = torch.zeros((resolution, resolution))
            final_image[border:border+target_size, border:border+target_size] = resized_image
            final_mask[border:border+target_size, border:border+target_size] = resized_mask

            final_images.append(final_image)
            final_masks.append(final_mask)

            # Step 4: Complete processing for this image
            progress_bar.update_absolute((i + 1) * 4)

        # Handle empty batch case
        if len(final_images) == 0:
            final_images = torch.zeros((output.shape[0], resolution, resolution, 4))
            final_masks = torch.zeros((output.shape[0], resolution, resolution))
        else:
            final_images = torch.stack(final_images, dim=0)
            final_masks = torch.stack(final_masks, dim=0)

        return (final_images, final_masks,)