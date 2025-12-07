import torch
from PIL import Image
from transformers import Florence2ForConditionalGeneration, Florence2Processor

MODEL_ID = "ducviet00/Florence-2-large-hf"
device = "cuda:0" if torch.cuda.is_available() else "cpu"
torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32


model = Florence2ForConditionalGeneration.from_pretrained(
    MODEL_ID, torch_dtype=torch_dtype
).to(device)
processor = Florence2Processor.from_pretrained(
    MODEL_ID, torch_dtype=torch_dtype, trust_remote_code=True
)


def get_task_response(task_prompt: str, image: Image.Image, text_input=None):
    """Return the associated task response

    Task can be:
        '<MORE_DETAILED_CAPTION>'
        '<DETAILED_CAPTION>'
        '<CAPTION>'

    """
    if text_input is None:
        prompt = task_prompt
    else:
        prompt = task_prompt + text_input
    inputs = processor(
        text=prompt,
        images=image,
        return_tensors="pt",
    ).to(device, torch_dtype)

    generated_ids = model.generate(
        input_ids=inputs["input_ids"],
        pixel_values=inputs["pixel_values"],
        max_new_tokens=1024,
        num_beams=3,
    )
    generated_text = processor.batch_decode(generated_ids, skip_special_tokens=False)[0]

    parsed_answer = processor.post_process_generation(
        generated_text, task=task_prompt, image_size=(image.width, image.height)
    )

    return parsed_answer[task_prompt]
