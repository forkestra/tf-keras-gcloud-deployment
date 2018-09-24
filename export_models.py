import os
import shutil
import tensorflow as tf
from tensorflow import keras


# Some parameters
HEIGHT = 128
WIDTH = 128
CHANNELS = 3
version = 'v1'

# First convert the .h5 keras model to a TF estimator model
h5_model_path = os.path.join('models/h5/best_model.h5')
tf_model_path = os.path.join('models/tf')
estimator = keras.estimator.model_to_estimator(
    keras_model_path=h5_model_path,
    model_dir=tf_model_path)


def image_preprocessing(image):
    """
    This implements the standard preprocessing that needs to be applied to the
    image tensors before passing them to the model. This is used for all input
    types.
    """
    image = tf.expand_dims(image, 0)
    image = tf.image.resize_bilinear(image, [HEIGHT, WIDTH], align_corners=False)
    image = tf.squeeze(image, axis=[0])
    image = tf.cast(image, dtype=tf.uint8)
    return image


#####################
# IMAGE AS LIST INPUT

model_input_is_uint8 = False  # Will not work correctly if set to True
if model_input_is_uint8:
    # This is the simplest way to save the model but does not allow for any
    # preprocessing of the image. For our model, the list representation would
    # have to have float values between 0 and 1, but this would make the JSON
    # file even bigger. The model could be adapted to accept uint8 values and
    # then have the conversions to [0,1] floats within the model. The code here
    # is just for illustration and completeness.
    model = keras.models.load_model(os.path.join(save_dir, 'best_model.h5'))
    export_path = os.path.join('models/json_list', version)
    keras.backend.set_learning_phase(0) # Ignore model parts only relevant to training
    with keras.backend.get_session() as sess:
        tf.saved_model.simple_save(
            sess,
            export_path,
            inputs={'image': model.input},
            outputs={'output': model.output})

else:

    def serving_input_receiver_fn():
        def prepare_image(image_str_tensor):
            #image = tf.decode_raw(image_str_tensor, out_type='uint8')
            #return image_preprocessing(image)
            return image_preprocessing(image_str_tensor)

        # TODO: verify if this works or fix it!!!

        #input_ph = tf.placeholder(tf.string, shape=[None])
        input_ph = tf.placeholder(tf.uint8, shape=[None,128,128,3])
        images_tensor = tf.map_fn(
            prepare_image, input_ph, back_prop=False, dtype=tf.uint8)
        images_tensor = tf.image.convert_image_dtype(images_tensor, dtype=tf.float32)

        return tf.estimator.export.ServingInputReceiver(
            {'input': images_tensor},
            {'image': input_ph})

    export_path = os.path.join('models/json_list', version)
    if os.path.exists(export_path):  # clean up old exports with this version
        shutil.rmtree(export_path)
    estimator.export_savedmodel(
        export_path,
        serving_input_receiver_fn=serving_input_receiver_fn)


#######################
# IMAGE AS BASE64 BYTES

def serving_input_receiver_fn():
    def prepare_image(image_str_tensor):
        image = tf.image.decode_jpeg(image_str_tensor, channels=CHANNELS)
        return image_preprocessing(image)

    input_ph = tf.placeholder(tf.string, shape=[None])
    images_tensor = tf.map_fn(
        prepare_image, input_ph, back_prop=False, dtype=tf.uint8)
    images_tensor = tf.image.convert_image_dtype(images_tensor, dtype=tf.float32)

    return tf.estimator.export.ServingInputReceiver(
        {'input': images_tensor},
        {'image_bytes': input_ph})

export_path = os.path.join('models/json_b64', version)
if os.path.exists(export_path):  # clean up old exports with this version
    shutil.rmtree(export_path)
estimator.export_savedmodel(
    export_path,
    serving_input_receiver_fn=serving_input_receiver_fn)


##############
# IMAGE AS URL

def serving_input_receiver_fn():
    def prepare_image(image_str_tensor):
        image_contents = tf.read_file(image_str_tensor)
        image = tf.image.decode_jpeg(image_contents, channels=CHANNELS)
        return image_preprocessing(image)

    input_ph = tf.placeholder(tf.string, shape=[None])
    images_tensor = tf.map_fn(
        prepare_image, input_ph, back_prop=False, dtype=tf.uint8)
    images_tensor = tf.image.convert_image_dtype(images_tensor, dtype=tf.float32)

    return tf.estimator.export.ServingInputReceiver(
        {'input': images_tensor},
        {'image_url': input_ph})

export_path = os.path.join('models/json_url', version)
if os.path.exists(export_path):  # clean up old exports with this version
    shutil.rmtree(export_path)
estimator.export_savedmodel(
    export_path,
    serving_input_receiver_fn=serving_input_receiver_fn)

