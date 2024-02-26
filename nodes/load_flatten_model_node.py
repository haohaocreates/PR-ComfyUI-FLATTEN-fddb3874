from einops import rearrange
import comfy.sd
import comfy.model_base
import folder_paths
import comfy.ldm.modules.diffusionmodules.openaimodel as openaimodel
from ..modules.unet import UNetModel as FlattenModel


class PatchBaseModel(comfy.model_base.BaseModel):
    def __init__(self, model_config, model_type=comfy.model_base.ModelType.EPS, device=None, unet_model=FlattenModel):
        super().__init__(model_config, model_type, device, FlattenModel)


class FlattenCheckpointLoaderNode:
    @classmethod
    def INPUT_TYPES(s):
        return {"required": {"ckpt_name": (folder_paths.get_filename_list("checkpoints"), ),
                             }}
    RETURN_TYPES = ("MODEL", "CLIP", "VAE")
    FUNCTION = "load_checkpoint"

    CATEGORY = "loaders"

    def load_checkpoint(self, ckpt_name, output_vae=True, output_clip=True):
        original_base = comfy.model_base.BaseModel
        comfy.model_base.BaseModel = PatchBaseModel
        ckpt_path = folder_paths.get_full_path("checkpoints", ckpt_name)
        out = comfy.sd.load_checkpoint_guess_config(
            ckpt_path, output_vae=True, output_clip=True, embedding_directory=folder_paths.get_folder_paths("embeddings"))
        comfy.model_base.BaseModel = original_base

        def model_function_wrapper(apply_model_func, apply_params):
            len_conds = len(apply_params['cond_or_uncond'])
            input_x = apply_params['input']
            input_x = rearrange(
                input_x, "(b f) c h w -> b c f h w", b=len_conds)
            timestep_ = apply_params['timestep']
            model_out = apply_model_func(input_x, timestep_, **apply_params)
            model_out = rearrange(model_out, 'b c f h w -> (b f) c h w')
            return model_out

        model = out[0]
        model.model_options['model_function_wrapper'] = model_function_wrapper

        return out[:3]
