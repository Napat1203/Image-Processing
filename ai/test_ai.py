"""Check the AI helpers without calling Forge or loading a model."""

import base64
import unittest

import numpy as np

from ai.controlnet import generate_from_pose
from ai.forge_client import ForgeError, prepare_prompt
from ai.process import process
from ai.remove_background import remove_background
from ai.segment import color_threshold, grow_part, recolor


class SegmentTests(unittest.TestCase):
    def test_grey_is_not_green(self):
        image = np.zeros((1, 2, 3), dtype=np.uint8)
        image[0, 0] = (85, 85, 85)
        image[0, 1] = (0, 255, 0)
        mask = color_threshold(image, (0, 255, 0), max_diff=10)
        self.assertEqual(int(mask[0, 0]), 0)
        self.assertEqual(int(mask[0, 1]), 255)

    def test_grow_part_stops_at_a_different_colour(self):
        image = np.full((1, 3, 3), 250, dtype=np.uint8)
        image[0, 2] = (0, 0, 255)
        mask = grow_part(image, 0, 0)
        self.assertEqual(int(mask[0, 0]), 255)
        self.assertEqual(int(mask[0, 1]), 255)
        self.assertEqual(int(mask[0, 2]), 0)

    def test_recolor_keeps_dark_pixels_dark(self):
        image = np.array([[[255, 255, 255], [10, 20, 30]]], dtype=np.uint8)
        mask = np.array([[255, 0]], dtype=np.uint8)
        painted = recolor(image, mask, (40, 170, 70))
        self.assertEqual(tuple(int(v) for v in painted[0, 0]), (40, 170, 70))
        self.assertEqual(tuple(int(v) for v in painted[0, 1]), (10, 20, 30))


class PromptTests(unittest.TestCase):
    def test_english_is_unchanged(self):
        self.assertEqual(prepare_prompt("a cat"), "a cat")

    def test_thai_uses_the_given_translator(self):
        self.assertEqual(prepare_prompt("แมว", translator=lambda text: "cat"), "cat")

    def test_empty_prompt_is_rejected(self):
        with self.assertRaises(ForgeError):
            prepare_prompt("  ")


class PoseTests(unittest.TestCase):
    def test_photo_and_skeleton_choose_different_modules(self):
        class FakeResponse:
            status_code = 200

            def json(self):
                return {"images": ["POSE"]}

        class FakeSession:
            def __init__(self):
                self.payloads = []

            def post(self, url, json=None, timeout=None):
                self.payloads.append(json)
                return FakeResponse()

        fake = FakeSession()
        generate_from_pose("a cat sitting", b"\x89PNG", session=fake)
        generate_from_pose(
            "a cat sitting",
            b"\x89PNG",
            already_skeleton=True,
            session=fake,
        )
        photo = fake.payloads[0]["alwayson_scripts"]["ControlNet"]["args"][0]
        skeleton = fake.payloads[1]["alwayson_scripts"]["ControlNet"]["args"][0]
        self.assertEqual(photo["module"], "openpose")
        self.assertEqual(skeleton["module"], "none")
        self.assertEqual(photo["model"], skeleton["model"])

    def test_empty_pose_image_is_rejected(self):
        with self.assertRaises(ForgeError):
            generate_from_pose("a cat", b"")


class ProcessTests(unittest.TestCase):
    def test_unknown_model_returns_the_same_bytes(self):
        result = process(b"abc", 7)
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["image_bytes"], b"abc")

    def test_remove_background_uses_the_cut_image(self):
        import ai.remove_background as bg

        bg.remove_background = lambda image_bytes: b"PNG"
        result = process(b"abc", 7, model="remove-background")
        self.assertEqual(result["image_bytes"], b"PNG")
        self.assertEqual(result["status"], "ok")

    def test_empty_image_is_rejected(self):
        with self.assertRaises(ValueError):
            remove_background(b"")

    def test_controlnet_without_prompt_is_an_error(self):
        result = process(b"abc", 7, model="controlnet")
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["image_bytes"], b"")

    def test_controlnet_returns_the_pose_image(self):
        import base64
        import ai.controlnet as pose
        pose.generate_from_pose = lambda prompt, image_bytes, already_skeleton=False: (
            base64.b64encode(b"POSE").decode("ascii")
        )
        result = process(
            b"abc",
            7,
            model="controlnet",
            prompt="a cat",
            already_skeleton=True,
        )
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["image_bytes"], b"POSE")

    def test_recolor_without_a_color_is_an_error(self):
        result = process(b"abc", 7, model="recolor", x=0, y=0)
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["image_bytes"], b"")

    def test_recolor_paints_only_the_clicked_part(self):
        import io

        import numpy as np
        from PIL import Image

        image = np.zeros((2, 2, 3), dtype=np.uint8)
        image[0, 0] = (255, 255, 255)
        image[0, 1] = (0, 0, 255)
        buf = io.BytesIO()
        Image.fromarray(image).save(buf, format="PNG")
        result = process(buf.getvalue(), 7, model="recolor", x=0, y=0, color="40,170,70")
        painted = np.array(Image.open(io.BytesIO(result["image_bytes"])).convert("RGB"))
        self.assertEqual(result["status"], "ok")
        self.assertEqual(tuple(int(v) for v in painted[0, 0]), (40, 170, 70))
        self.assertEqual(tuple(int(v) for v in painted[0, 1]), (0, 0, 255))
    def test_inpaint_without_a_click_is_an_error(self):
        result = process(b"abc", 7, model="inpaint", prompt="a red shirt")
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["image_bytes"], b"")

    def test_inpaint_returns_the_edited_image(self):
        import ai.inpaint as edit

        edit.inpaint_part = lambda prompt, image_bytes, x, y: (
            base64.b64encode(b"EDIT").decode("ascii")
        )
        result = process(
            b"abc",
            7,
            model="inpaint",
            prompt="a red shirt",
            x=1,
            y=2,
        )
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["image_bytes"], b"EDIT")
        
if __name__ == "__main__":
    unittest.main()