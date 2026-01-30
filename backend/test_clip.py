"""Test CLIP embedding generation."""
import torch
from transformers import CLIPModel, CLIPProcessor

model = CLIPModel.from_pretrained('openai/clip-vit-base-patch32')
processor = CLIPProcessor.from_pretrained('openai/clip-vit-base-patch32')

text = 'laptop computer'
inputs = processor(text=[text], return_tensors='pt', padding=True)
text_inputs = {k: v for k, v in inputs.items() if k != 'pixel_values'}
outputs = model.get_text_features(**text_inputs)

print('Type:', type(outputs))
print('Is tensor:', isinstance(outputs, torch.Tensor))

if isinstance(outputs, torch.Tensor):
    print('Shape:', outputs.shape)
    emb = outputs / outputs.norm(p=2, dim=-1, keepdim=True)
    print('First 5:', emb[0][:5].tolist())
else:
    print('Has pooler_output:', hasattr(outputs, 'pooler_output'))
    print('Has last_hidden_state:', hasattr(outputs, 'last_hidden_state'))
    if hasattr(outputs, 'pooler_output') and outputs.pooler_output is not None:
        pooled = outputs.pooler_output
        print('pooler_output shape:', pooled.shape)
    elif hasattr(outputs, 'last_hidden_state'):
        lhs = outputs.last_hidden_state
        print('last_hidden_state shape:', lhs.shape)
        # Use mean pooling
        emb = lhs.mean(dim=1)
        emb = emb / emb.norm(p=2, dim=-1, keepdim=True)
        print('Embedding shape:', emb.shape)
        print('First 5:', emb[0][:5].tolist())
