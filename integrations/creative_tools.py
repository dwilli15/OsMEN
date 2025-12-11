#!/usr/bin/env python3
"""
OsMEN Creative Tools Integration

Provides:
- InvokeAI integration (Stable Diffusion)
- ComfyUI integration (planned)
- Text-to-3D pipeline (research)
- Clipchamp/Canva (research - web APIs)

Usage:
    from integrations.creative_tools import CreativeIntegration

    creative = CreativeIntegration()

    # Generate image
    result = await creative.generate_image("A sunset over mountains")
"""

import asyncio
import base64
import json
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import aiohttp

logger = logging.getLogger(__name__)


# ============================================================================
# Configuration
# ============================================================================


@dataclass
class CreativeConfig:
    """Creative tools configuration"""

    # InvokeAI
    invokeai_url: str = "http://localhost:9090"
    invokeai_api_key: Optional[str] = None

    # ComfyUI
    comfyui_url: str = "http://localhost:8188"

    # Default generation settings
    default_model: str = "stable-diffusion-xl-base-1-0"
    default_steps: int = 30
    default_cfg_scale: float = 7.5
    default_width: int = 1024
    default_height: int = 1024

    @classmethod
    def from_env(cls) -> "CreativeConfig":
        """Load from environment"""
        return cls(
            invokeai_url=os.getenv("INVOKEAI_URL", "http://localhost:9090"),
            comfyui_url=os.getenv("COMFYUI_URL", "http://localhost:8188"),
        )


# ============================================================================
# InvokeAI Integration
# ============================================================================


class InvokeAIClient:
    """InvokeAI API client"""

    def __init__(self, config: CreativeConfig):
        self.config = config
        self.base_url = config.invokeai_url
        self.available = False
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def check_health(self) -> bool:
        """Check if InvokeAI is available"""
        try:
            session = await self._get_session()
            async with session.get(
                f"{self.base_url}/api/v1/app/version", timeout=5
            ) as response:
                if response.status == 200:
                    self.available = True
                    return True
        except Exception as e:
            logger.debug(f"InvokeAI not available: {e}")

        self.available = False
        return False

    async def get_models(self) -> Dict[str, Any]:
        """Get available models"""
        try:
            session = await self._get_session()
            async with session.get(f"{self.base_url}/api/v2/models/") as response:
                if response.status == 200:
                    return await response.json()
        except Exception as e:
            logger.error(f"Failed to get models: {e}")

        return {"models": []}

    async def generate_image(
        self,
        prompt: str,
        negative_prompt: str = "",
        model: Optional[str] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
        steps: Optional[int] = None,
        cfg_scale: Optional[float] = None,
        seed: int = -1,
        output_path: Optional[Union[str, Path]] = None,
    ) -> Dict[str, Any]:
        """Generate image using InvokeAI"""
        if not await self.check_health():
            return {"error": "InvokeAI not available"}

        # Build generation request
        graph = {
            "id": "text_to_image",
            "nodes": {
                "main_model_loader": {
                    "type": "main_model_loader",
                    "id": "main_model_loader",
                    "model": {
                        "model_name": model or self.config.default_model,
                        "base_model": "sdxl",
                        "model_type": "main",
                    },
                },
                "clip_skip": {
                    "type": "clip_skip",
                    "id": "clip_skip",
                    "skipped_layers": 0,
                },
                "positive_conditioning": {
                    "type": "compel",
                    "id": "positive_conditioning",
                    "prompt": prompt,
                },
                "negative_conditioning": {
                    "type": "compel",
                    "id": "negative_conditioning",
                    "prompt": negative_prompt or "blurry, low quality, distorted",
                },
                "noise": {
                    "type": "noise",
                    "id": "noise",
                    "seed": seed,
                    "width": width or self.config.default_width,
                    "height": height or self.config.default_height,
                    "use_cpu": False,
                },
                "denoise_latents": {
                    "type": "denoise_latents",
                    "id": "denoise_latents",
                    "steps": steps or self.config.default_steps,
                    "cfg_scale": cfg_scale or self.config.default_cfg_scale,
                    "denoising_start": 0,
                    "denoising_end": 1,
                },
                "latents_to_image": {"type": "l2i", "id": "latents_to_image"},
                "save_image": {
                    "type": "save_image",
                    "id": "save_image",
                    "is_intermediate": False,
                },
            },
            "edges": [
                {
                    "source": {"node_id": "main_model_loader", "field": "unet"},
                    "destination": {"node_id": "denoise_latents", "field": "unet"},
                },
                {
                    "source": {"node_id": "main_model_loader", "field": "clip"},
                    "destination": {"node_id": "clip_skip", "field": "clip"},
                },
                {
                    "source": {"node_id": "clip_skip", "field": "clip"},
                    "destination": {
                        "node_id": "positive_conditioning",
                        "field": "clip",
                    },
                },
                {
                    "source": {"node_id": "clip_skip", "field": "clip"},
                    "destination": {
                        "node_id": "negative_conditioning",
                        "field": "clip",
                    },
                },
                {
                    "source": {
                        "node_id": "positive_conditioning",
                        "field": "conditioning",
                    },
                    "destination": {
                        "node_id": "denoise_latents",
                        "field": "positive_conditioning",
                    },
                },
                {
                    "source": {
                        "node_id": "negative_conditioning",
                        "field": "conditioning",
                    },
                    "destination": {
                        "node_id": "denoise_latents",
                        "field": "negative_conditioning",
                    },
                },
                {
                    "source": {"node_id": "noise", "field": "noise"},
                    "destination": {"node_id": "denoise_latents", "field": "noise"},
                },
                {
                    "source": {"node_id": "denoise_latents", "field": "latents"},
                    "destination": {"node_id": "latents_to_image", "field": "latents"},
                },
                {
                    "source": {"node_id": "main_model_loader", "field": "vae"},
                    "destination": {"node_id": "latents_to_image", "field": "vae"},
                },
                {
                    "source": {"node_id": "latents_to_image", "field": "image"},
                    "destination": {"node_id": "save_image", "field": "image"},
                },
            ],
        }

        try:
            session = await self._get_session()

            # Enqueue the generation
            async with session.post(
                f"{self.base_url}/api/v1/queue/default/enqueue_graph",
                json={"graph": graph, "prepend": False},
            ) as response:
                if response.status != 200:
                    return {"error": f"Failed to enqueue: {await response.text()}"}

                result = await response.json()
                batch_id = result.get("batch", {}).get("batch_id")

            # Poll for completion
            for _ in range(120):  # Max 2 minutes
                await asyncio.sleep(1)

                async with session.get(
                    f"{self.base_url}/api/v1/queue/default/status"
                ) as status_response:
                    status = await status_response.json()

                    # Check if our batch is complete
                    if status.get("queue", {}).get("pending", 0) == 0:
                        break

            # Get the generated image
            async with session.get(
                f"{self.base_url}/api/v1/images/?board_id=none&limit=1"
            ) as images_response:
                images = await images_response.json()

                if images.get("items"):
                    image_name = images["items"][0]["image_name"]

                    # Download image
                    async with session.get(
                        f"{self.base_url}/api/v1/images/i/{image_name}/full"
                    ) as img_response:
                        if img_response.status == 200:
                            image_data = await img_response.read()

                            if output_path:
                                with open(output_path, "wb") as f:
                                    f.write(image_data)

                                return {
                                    "success": True,
                                    "output_path": str(output_path),
                                    "image_name": image_name,
                                    "prompt": prompt,
                                }
                            else:
                                return {
                                    "success": True,
                                    "image_name": image_name,
                                    "image_base64": base64.b64encode(
                                        image_data
                                    ).decode(),
                                    "prompt": prompt,
                                }

            return {"error": "Generation completed but image not found"}

        except Exception as e:
            logger.error(f"Image generation failed: {e}")
            return {"error": str(e)}

    async def close(self):
        """Close the session"""
        if self._session:
            await self._session.close()


# ============================================================================
# ComfyUI Integration (Placeholder)
# ============================================================================


class ComfyUIClient:
    """ComfyUI API client (placeholder for future implementation)"""

    def __init__(self, config: CreativeConfig):
        self.config = config
        self.base_url = config.comfyui_url
        self.available = False

    async def check_health(self) -> bool:
        """Check if ComfyUI is available"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/system_stats", timeout=5
                ) as response:
                    if response.status == 200:
                        self.available = True
                        return True
        except:
            pass

        self.available = False
        return False

    async def run_workflow(
        self, workflow: Dict[str, Any], inputs: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Run a ComfyUI workflow (placeholder)"""
        if not await self.check_health():
            return {"error": "ComfyUI not available"}

        # TODO: Implement ComfyUI workflow execution
        return {"error": "ComfyUI integration not yet implemented"}


# ============================================================================
# Text-to-3D Integration (Research/Placeholder)
# ============================================================================


class Text3DClient:
    """Text-to-3D generation client

    Research options:
    - OpenAI Shap-E (local)
    - Meshy.ai (API)
    - Stable Diffusion + depth estimation + mesh
    """

    def __init__(self, config: CreativeConfig):
        self.config = config
        self.available = False
        self._check_availability()

    def _check_availability(self):
        """Check if text-to-3D is available"""
        # Check for Shap-E
        try:
            import torch
            from shap_e.diffusion.sample import sample_latents

            self.available = True
            self.backend = "shap_e"
            logger.info("Shap-E text-to-3D available")
        except ImportError:
            logger.debug("Shap-E not installed")

        # Could add Meshy.ai API check here

    async def generate_3d(
        self,
        prompt: str,
        output_path: Union[str, Path],
        format: str = "stl",  # stl, obj, ply, glb
    ) -> Dict[str, Any]:
        """Generate 3D model from text"""
        if not self.available:
            return {
                "error": "Text-to-3D not available. Install shap-e or configure Meshy.ai API."
            }

        if self.backend == "shap_e":
            return await self._generate_shap_e(prompt, output_path, format)

        return {"error": "No text-to-3D backend configured"}

    async def _generate_shap_e(
        self, prompt: str, output_path: Union[str, Path], format: str
    ) -> Dict[str, Any]:
        """Generate using Shap-E"""
        try:
            import torch
            from shap_e.diffusion.gaussian_diffusion import diffusion_from_config
            from shap_e.diffusion.sample import sample_latents
            from shap_e.models.download import load_config, load_model
            from shap_e.util.notebooks import decode_latent_mesh

            device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

            # Load models
            xm = load_model("transmitter", device=device)
            model = load_model("text300M", device=device)
            diffusion = diffusion_from_config(load_config("diffusion"))

            # Generate latents
            latents = sample_latents(
                batch_size=1,
                model=model,
                diffusion=diffusion,
                guidance_scale=15.0,
                model_kwargs=dict(texts=[prompt]),
                progress=True,
                clip_denoised=True,
                use_fp16=True,
                use_karras=True,
                karras_steps=64,
                sigma_min=1e-3,
                sigma_max=160,
                s_churn=0,
            )

            # Decode to mesh
            mesh = decode_latent_mesh(xm, latents[0]).tri_mesh()

            # Export to requested format
            output_path = Path(output_path)

            if format == "stl":
                mesh.write_stl(output_path)
            elif format == "obj":
                mesh.write_obj(output_path)
            elif format == "ply":
                mesh.write_ply(output_path)
            elif format == "glb":
                # GLB requires trimesh
                import trimesh

                tm = trimesh.Trimesh(vertices=mesh.verts, faces=mesh.faces)
                tm.export(output_path)
            else:
                return {"error": f"Unknown format: {format}"}

            return {
                "success": True,
                "output_path": str(output_path),
                "prompt": prompt,
                "format": format,
            }

        except Exception as e:
            logger.error(f"Shap-E generation failed: {e}")
            return {"error": str(e)}


# ============================================================================
# Unified Creative Integration
# ============================================================================


class CreativeIntegration:
    """Unified creative tools integration"""

    def __init__(self, config: Optional[CreativeConfig] = None):
        self.config = config or CreativeConfig.from_env()
        self.invokeai = InvokeAIClient(self.config)
        self.comfyui = ComfyUIClient(self.config)
        self.text3d = Text3DClient(self.config)

    async def get_status(self) -> Dict[str, Any]:
        """Get integration status"""
        invokeai_healthy = await self.invokeai.check_health()
        comfyui_healthy = await self.comfyui.check_health()

        return {
            "invokeai": {
                "url": self.config.invokeai_url,
                "available": invokeai_healthy,
            },
            "comfyui": {"url": self.config.comfyui_url, "available": comfyui_healthy},
            "text_to_3d": {
                "available": self.text3d.available,
                "backend": getattr(self.text3d, "backend", None),
            },
        }

    async def generate_image(
        self, prompt: str, output_path: Optional[str] = None, **kwargs
    ) -> Dict[str, Any]:
        """Generate image using best available backend"""
        # Try InvokeAI first
        if await self.invokeai.check_health():
            return await self.invokeai.generate_image(
                prompt, output_path=output_path, **kwargs
            )

        # Could add ComfyUI fallback here

        return {"error": "No image generation backend available"}

    async def generate_3d(
        self, prompt: str, output_path: str, format: str = "stl"
    ) -> Dict[str, Any]:
        """Generate 3D model from text"""
        return await self.text3d.generate_3d(prompt, output_path, format)

    async def get_models(self) -> Dict[str, Any]:
        """Get available models"""
        models = {}

        if await self.invokeai.check_health():
            models["invokeai"] = await self.invokeai.get_models()

        return models

    async def close(self):
        """Clean up resources"""
        await self.invokeai.close()


# ============================================================================
# MCP Tool Handlers
# ============================================================================

_creative: Optional[CreativeIntegration] = None


def get_creative() -> CreativeIntegration:
    """Get or create creative integration"""
    global _creative
    if _creative is None:
        _creative = CreativeIntegration()
    return _creative


async def handle_generate_image(params: Dict[str, Any]) -> Dict[str, Any]:
    """MCP handler for image generation"""
    creative = get_creative()

    prompt = params.get("prompt")
    if not prompt:
        return {"error": "prompt required"}

    return await creative.generate_image(
        prompt=prompt,
        negative_prompt=params.get("negative_prompt", ""),
        output_path=params.get("output_path"),
        width=params.get("width"),
        height=params.get("height"),
        steps=params.get("steps"),
        cfg_scale=params.get("cfg_scale"),
        seed=params.get("seed", -1),
    )


async def handle_generate_3d(params: Dict[str, Any]) -> Dict[str, Any]:
    """MCP handler for 3D generation"""
    creative = get_creative()

    prompt = params.get("prompt")
    output_path = params.get("output_path")

    if not prompt:
        return {"error": "prompt required"}
    if not output_path:
        return {"error": "output_path required"}

    return await creative.generate_3d(
        prompt=prompt, output_path=output_path, format=params.get("format", "stl")
    )


async def handle_creative_status(params: Dict[str, Any]) -> Dict[str, Any]:
    """MCP handler for creative status"""
    creative = get_creative()
    return await creative.get_status()


async def handle_list_models(params: Dict[str, Any]) -> Dict[str, Any]:
    """MCP handler for listing models"""
    creative = get_creative()
    return await creative.get_models()


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":

    async def main():
        creative = CreativeIntegration()
        print("Creative Integration Status:")
        status = await creative.get_status()
        print(json.dumps(status, indent=2))

        # Test image generation if available
        if status["invokeai"]["available"]:
            print("\nGenerating test image...")
            result = await creative.generate_image(
                "A beautiful sunset over mountains, digital art",
                output_path="test_image.png",
            )
            print(
                json.dumps(
                    {k: v for k, v in result.items() if k != "image_base64"}, indent=2
                )
            )

        await creative.close()

    asyncio.run(main())
    asyncio.run(main())
    asyncio.run(main())
