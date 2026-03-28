import tensorflow as tf
import tf2onnx
from tensorflow.keras.models import load_model

model = load_model('Nail_disease_model_1.h5', compile=False)
spec = (tf.TensorSpec((None, 128, 128, 3), tf.float32, name="input"),)
output_path = "Nail_disease_model_1.onnx"
model_proto, _ = tf2onnx.convert.from_keras(model, input_signature=spec, opset=13, output_path=output_path)
print("Saved ONNX model to", output_path)
