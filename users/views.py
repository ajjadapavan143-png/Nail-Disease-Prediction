from django.shortcuts import render
from django.contrib import messages
from django.conf import settings
from django.core.files.base import ContentFile
import os
import json
import io
import base64
import uuid
import numpy as np
from PIL import Image

# IMPORTANT: Tkinter crash avoid cheyyadaniki backend set cheyyali
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from .forms import UserRegistrationForm
from .models import UserRegistrationModel, PredictionHistory


# =========================
# USER REGISTER
# =========================
def UserRegisterActions(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'You have been successfully registered')
            form = UserRegistrationForm()
            return render(request, 'UserRegistrations.html', {'form': form})
        else:
            messages.error(request, 'Email or Mobile Already Existed')
    else:
        form = UserRegistrationForm()

    return render(request, 'UserRegistrations.html', {'form': form})


# =========================
# USER LOGIN
# =========================
def UserLoginCheck(request):
    if request.method == "POST":
        loginid = request.POST.get('loginid')
        pswd = request.POST.get('pswd')

        try:
            check = UserRegistrationModel.objects.get(loginid=loginid, password=pswd)
            status = str(check.status).strip().lower()

            if status == "activated":
                request.session['id'] = check.id
                request.session['loggeduser'] = check.name
                request.session['loginid'] = check.loginid
                request.session['email'] = check.email

                return render(request, 'users/UserHomePage.html', {})
            else:
                messages.error(request, 'Your Account is not activated')
                return render(request, 'UserLogin.html', {})

        except UserRegistrationModel.DoesNotExist:
            messages.error(request, 'Invalid Login ID or Password')
            return render(request, 'UserLogin.html', {})

        except Exception as e:
            print("Login Error:", str(e))
            messages.error(request, f'Error: {str(e)}')
            return render(request, 'UserLogin.html', {})

    return render(request, 'UserLogin.html', {})


# =========================
# USER HOME
# =========================
def UserHome(request):
    return render(request, 'users/UserHomePage.html', {})


# =========================
# TRAINING
# =========================
def training(request):
    try:
        import tensorflow as tf
        from tensorflow.keras.preprocessing.image import ImageDataGenerator
        from tensorflow.keras.applications import DenseNet121
        from tensorflow.keras.models import Model
        from tensorflow.keras.layers import Dense, Dropout, GlobalAveragePooling2D
        from tensorflow.keras.optimizers import Adam
        from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint, ReduceLROnPlateau
    except Exception as e:
        messages.error(request, f"TensorFlow import error: {str(e)}")
        return render(request, 'users/training.html', {})

    train_path = os.path.join(settings.MEDIA_ROOT, 'data', 'train')
    validation_path = os.path.join(settings.MEDIA_ROOT, 'data', 'validation')

    if not os.path.exists(train_path):
        messages.error(request, f"Train folder not found: {train_path}")
        return render(request, 'users/training.html', {})

    if not os.path.exists(validation_path):
        messages.error(request, f"Validation folder not found: {validation_path}")
        return render(request, 'users/training.html', {})

    def preprocess_image(image_path, size=(128, 128)):
        img = tf.io.read_file(image_path)
        img = tf.image.decode_image(img, channels=3, expand_animations=False)
        img = tf.image.resize(img, size)
        img = img / 255.0
        return img

    def save_image(image_array, save_path):
        image_array = (image_array * 255).astype(np.uint8)
        img_pil = Image.fromarray(image_array)
        img_pil.save(save_path)

    def preprocess_and_save_images(folder_path, save_dir, size=(128, 128)):
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)

        for root, _, files in os.walk(folder_path):
            for filename in files:
                img_path = os.path.join(root, filename)

                if os.path.isfile(img_path):
                    try:
                        preprocessed_img = preprocess_image(img_path, size)
                        rel_path = os.path.relpath(img_path, folder_path)
                        save_path = os.path.join(save_dir, rel_path)

                        os.makedirs(os.path.dirname(save_path), exist_ok=True)
                        save_image(preprocessed_img.numpy(), save_path)
                    except Exception as e:
                        print("Skipped bad image:", img_path, str(e))
                        continue

    preprocess_and_save_images(train_path, train_path)
    preprocess_and_save_images(validation_path, validation_path)

    def create_image_dataset(directory, img_size=(128, 128), batch_size=16):
        datagen = ImageDataGenerator(
            rescale=1.0 / 255,
            rotation_range=20,
            width_shift_range=0.2,
            height_shift_range=0.2,
            shear_range=0.2,
            zoom_range=0.2,
            horizontal_flip=True,
            fill_mode='nearest'
        )

        return datagen.flow_from_directory(
            directory,
            target_size=img_size,
            batch_size=batch_size,
            class_mode='categorical',
            shuffle=True
        )

    try:
        train_dataset = create_image_dataset(train_path)
        val_dataset = create_image_dataset(validation_path)

        print("Class Indices =", train_dataset.class_indices)

        sorted_class_labels = list(train_dataset.class_indices.keys())
        labels_path = os.path.join(settings.BASE_DIR, 'class_labels.json')

        with open(labels_path, 'w') as f:
            json.dump(sorted_class_labels, f)

        print("Class labels saved:", sorted_class_labels)

        def create_densenet_model(input_shape, num_classes):
            base_model = DenseNet121(include_top=False, weights='imagenet', input_shape=input_shape)
            base_model.trainable = False

            x = base_model.output
            x = GlobalAveragePooling2D()(x)
            x = Dense(256, activation='relu')(x)
            x = Dropout(0.5)(x)
            predictions = Dense(num_classes, activation='softmax')(x)

            model = Model(inputs=base_model.input, outputs=predictions)
            model.compile(
                optimizer=Adam(learning_rate=1e-3),
                loss='categorical_crossentropy',
                metrics=['accuracy']
            )
            return model

        input_shape = (128, 128, 3)
        num_classes = len(train_dataset.class_indices)
        model = create_densenet_model(input_shape, num_classes)

        early_stopping = EarlyStopping(monitor='val_loss', patience=5, restore_best_weights=True)
        checkpoint = ModelCheckpoint(
            os.path.join(settings.BASE_DIR, 'best_model.keras'),
            monitor='val_loss',
            save_best_only=True
        )
        reduce_lr = ReduceLROnPlateau(monitor='val_loss', factor=0.2, patience=3, min_lr=1e-6)

        history = model.fit(
            train_dataset,
            validation_data=val_dataset,
            epochs=300,
            verbose=1,
            callbacks=[early_stopping, checkpoint, reduce_lr]
        )

        val_loss, val_accuracy = model.evaluate(val_dataset, verbose=0)

        model_save_path = os.path.join(settings.BASE_DIR, 'Nail_disease_model_1.keras')
        model.save(model_save_path)
        print("Model saved at:", model_save_path)

        def plot_history(history_obj):
            plt.figure(figsize=(12, 5))

            plt.subplot(1, 2, 1)
            plt.plot(history_obj.history['accuracy'])
            plt.plot(history_obj.history['val_accuracy'])
            plt.title('Model Accuracy')
            plt.xlabel('Epoch')
            plt.ylabel('Accuracy')
            plt.legend(['Train', 'Validation'])
            plt.grid()

            plt.subplot(1, 2, 2)
            plt.plot(history_obj.history['loss'])
            plt.plot(history_obj.history['val_loss'])
            plt.title('Model Loss')
            plt.xlabel('Epoch')
            plt.ylabel('Loss')
            plt.legend(['Train', 'Validation'])
            plt.grid()

            plt.tight_layout()

            plot_folder = os.path.join(settings.BASE_DIR, 'static', 'plots')
            os.makedirs(plot_folder, exist_ok=True)

            plot_path = os.path.join(plot_folder, 'training_plot.png')
            plt.savefig(plot_path)
            plt.close()

        plot_history(history)

        global loaded_model, loaded_class_labels
        loaded_model = None
        loaded_class_labels = None

        context = {
            'val_accuracy': round(val_accuracy * 100, 2),
            'val_loss': round(val_loss, 4),
            'plot_url': '/static/plots/training_plot.png'
        }

        return render(request, 'users/training.html', context)

    except Exception as e:
        print("Training Error:", str(e))
        messages.error(request, f"Training failed: {str(e)}")
        return render(request, 'users/training.html', {})


# =========================
# MODEL + LABELS LAZY LOAD
# =========================
loaded_model = None
loaded_class_labels = None


def get_model_and_labels():
    global loaded_model, loaded_class_labels

    try:
        if loaded_model is None:
            tflite_path = os.path.join(settings.BASE_DIR, "Nail_disease_model_1.tflite")
            print("Trying to load TFLite model from:", tflite_path)

            if os.path.exists(tflite_path):
                try:
                    import tflite_runtime.interpreter as tflite
                    loaded_model = tflite.Interpreter(model_path=tflite_path)
                    print("loaded tflite_runtime interpreter")
                except ImportError:
                    os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
                    import tensorflow as tf
                    loaded_model = tf.lite.Interpreter(model_path=tflite_path)
                    print("loaded tensorflow tf.lite interpreter")
                    
                loaded_model.allocate_tensors()
                print("TFLite Model loaded successfully")
            else:
                print("TFLite Model file NOT FOUND")
                loaded_model = None

        if loaded_class_labels is None:
            labels_path = os.path.join(settings.BASE_DIR, "class_labels.json")

            if os.path.exists(labels_path):
                with open(labels_path, 'r') as f:
                    loaded_class_labels = json.load(f)
                print("Loaded class labels:", loaded_class_labels)
            else:
                print("class_labels.json NOT FOUND")
                loaded_class_labels = []

    except Exception as e:
        print("Model loading error:", str(e))
        loaded_model = None
        loaded_class_labels = []

    return loaded_model, loaded_class_labels


# =========================
# IMAGE PREPROCESS
# =========================
def load_and_preprocess_image(img):
    try:
        img = img.resize((128, 128), Image.Resampling.LANCZOS)
        # Replaced tensorflow.keras import with pure numpy to avoid immense RAM consumption
        img_array = np.array(img, dtype=np.float32)
        img_array = img_array / 255.0
        img_array = np.expand_dims(img_array, axis=0)
        return img_array
    except Exception as e:
        print("Image preprocess error:", str(e))
        return None


# =========================
# SAVE PREDICTION HISTORY
# =========================
def save_prediction_history(request, img, predicted_class, confidence, source_type):
    try:
        loginid = request.session.get('loginid', 'Unknown')
        username = request.session.get('loggeduser', 'Unknown')

        img_io = io.BytesIO()
        img = img.convert('RGB')
        img.save(img_io, format='JPEG')
        img_file = ContentFile(img_io.getvalue(), name=f"{uuid.uuid4().hex}.jpg")

        PredictionHistory.objects.create(
            loginid=loginid,
            username=username,
            predicted_class=predicted_class,
            confidence=confidence,
            prediction_image=img_file,
            source=source_type
        )

        print("Prediction history saved successfully")

    except Exception as e:
        print("Prediction history save error:", str(e))


# =========================
# COMMON PREDICTION FUNCTION
# =========================
def process_prediction_image(img, request, source_type='upload'):
    try:
        model, class_labels = get_model_and_labels()

        if model is None:
            messages.error(request, "Model file not found or failed to load on server.")
            return None, True

        if not class_labels:
            messages.error(request, "Class labels file not found. Please train model again.")
            return None, True

        img = img.convert('RGB')
        img_array = load_and_preprocess_image(img)

        if img_array is None:
            messages.error(request, "Image preprocessing failed.")
            return None, True

        if hasattr(model, 'invoke'):
            input_details = model.get_input_details()
            output_details = model.get_output_details()
            
            img_array = img_array.astype(np.float32)
            model.set_tensor(input_details[0]['index'], img_array)
            model.invoke()
            prediction = model.get_tensor(output_details[0]['index'])
        else:
            prediction = model.predict(img_array, verbose=0)
            
        predicted_index = np.argmax(prediction)
        predicted_class = class_labels[predicted_index]
        confidence = float(np.max(prediction) * 100)

        print("Predicted Class =", predicted_class)
        print("Confidence =", confidence)

        if source_type == 'camera':
            if predicted_class == "Not_Nail" and confidence > 85:
                messages.error(request, "Invalid Image. Please capture a clear nail image only.")
                return None, True

            if predicted_class == "Healthy_Nail":
                predicted_class = "have no disease"

            confidence_str = f"{confidence:.2f}"
            if predicted_class == "have no disease":
                confidence_str = ""
        else:
            if predicted_class == "Not_Nail" or confidence < 45:
                messages.error(request, "Invalid Nail Image. Please upload a clear nail image only.")
                return None, True

            if predicted_class == "Healthy_Nail":
                predicted_class = "have no disease"

            confidence_str = f"{confidence:.2f}"

        save_prediction_history(request, img, predicted_class, confidence_str, source_type)

        buffered = io.BytesIO()
        img.save(buffered, format="JPEG")
        img_str = base64.b64encode(buffered.getvalue()).decode()

        context = {
            'predicted_class': predicted_class,
            'confidence': confidence_str,
            'image_data': img_str,
        }

        return context, False

    except Exception as e:
        print("Prediction Error:", str(e))
        messages.error(request, f"Prediction failed: {str(e)}")
        return None, True


# =========================
# NAIL PREDICTION (UPLOAD + CAMERA)
# =========================
def nail_prediction_view(request):
    context = {}

    # GET request ki just page open cheyyali
    if request.method != 'POST':
        return render(request, 'users/nail_prediction.html', context)

    try:
        # CAMERA IMAGE HANDLE
        captured_image = request.POST.get('captured_image')

        if captured_image:
            try:
                if ';base64,' not in captured_image:
                    messages.error(request, "Captured image format invalid. Please capture again.")
                    return render(request, 'users/nail_prediction.html', context)

                _, imgstr = captured_image.split(';base64,')
                image_data = base64.b64decode(imgstr)
                img = Image.open(io.BytesIO(image_data))

                result_context, has_error = process_prediction_image(img, request, source_type='camera')
                if not has_error and result_context:
                    return render(request, 'users/nail_prediction.html', result_context)

                return render(request, 'users/nail_prediction.html', context)

            except Exception as e:
                print("Camera Prediction Error:", str(e))
                messages.error(request, f"Captured image error: {str(e)}")
                return render(request, 'users/nail_prediction.html', context)

        # FILE UPLOAD HANDLE
        uploaded_file = request.FILES.get('nail_image')

        if not uploaded_file:
            messages.error(request, "Please upload a nail image or use live camera.")
            return render(request, 'users/nail_prediction.html', context)

        valid_extensions = ['.jpg', '.jpeg', '.png']
        file_ext = os.path.splitext(uploaded_file.name)[1].lower()

        if file_ext not in valid_extensions:
            messages.error(request, "Invalid file type. Upload only JPG, JPEG, PNG images.")
            return render(request, 'users/nail_prediction.html', context)

        try:
            img = Image.open(uploaded_file)
            result_context, has_error = process_prediction_image(img, request, source_type='upload')

            if not has_error and result_context:
                return render(request, 'users/nail_prediction.html', result_context)

        except Exception as e:
            print("Upload Prediction Error:", str(e))
            messages.error(request, f"Upload image error: {str(e)}")

    except Exception as e:
        print("nail_prediction_view Error:", str(e))
        messages.error(request, f"Page error: {str(e)}")

    return render(request, 'users/nail_prediction.html', context)


# =========================
# USER PREDICTION HISTORY
# =========================
def UserPredictionHistory(request):
    loginid = request.session.get('loginid')
    if not loginid:
        return render(request, 'UserLogin.html', {})

    history = PredictionHistory.objects.filter(loginid=loginid).order_by('-created_at')
    return render(request, 'users/user_prediction_history.html', {'history': history})