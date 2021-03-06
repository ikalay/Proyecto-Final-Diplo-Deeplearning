# -*- coding: utf-8 -*-
"""Trabajo Final CNN - Style Transfer Kalaydjian.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1wGv1opXKkYQJ_10hBNg6kB_q2gmq3rRI

# Style Transfer

<img src="https://i0.wp.com/chelseatroy.com/wp-content/uploads/2018/12/neural_style_transfer.png?resize=768%2C311&ssl=1">

La idea de este trabajo final es reproducir el siguiente paper:

https://arxiv.org/pdf/1508.06576.pdf

El objetivo es transferir el estilo de una imagen dada a otra imagen distinta. 

Como hemos visto en clase, las primeras capas de una red convolucional se activan ante la presencia de ciertos patrones vinculados a detalles muy pequeños.

A medida que avanzamos en las distintas capas de una red neuronal convolucional, los filtros se van activando a medida que detectan patrones de formas cada vez mas complejos.

Lo que propone este paper es asignarle a la activación de las primeras capas de una red neuronal convolucional (por ejemplo VGG19) la definición del estilo y a la activación de las últimas capas de la red neuronal convolucional, la definición del contenido.

La idea de este paper es, a partir de dos imágenes (una que aporte el estilo y otra que aporte el contenido) analizar cómo es la activación de las primeras capas para la imagen que aporta el estilo y cómo es la activación de las últimas capas de la red convolucional para la imagen que aporta el contenido. A partir de esto se intentará sintetizar una imagen que active los filtros de las primeras capas que se activaron con la imagen que aporta el estilo y los filtros de las últimas capas que se activaron con la imagen que aporta el contenido.

A este procedimiento se lo denomina neural style transfer.

# En este trabajo se deberá leer el paper mencionado y en base a ello, entender la implementación que se muestra a continuación y contestar preguntas sobre la misma.

# Una metodología posible es hacer una lectura rápida del paper (aunque esto signifique no entender algunos detalles del mismo) y luego ir analizando el código y respondiendo las preguntas. A medida que se planteen las preguntas, volviendo a leer secciones específicas del paper terminará de entender los detalles que pudieran haber quedado pendientes.

Lo primero que haremos es cargar dos imágenes, una que aporte el estilo y otra que aporte el contenido. A tal fin utilizaremos imágenes disponibles en la web.
"""

# Imagen para estilo
!wget https://upload.wikimedia.org/wikipedia/commons/5/52/La_noche_estrellada1.jpg

# Imagen para contenido
!wget https://upload.wikimedia.org/wikipedia/commons/thumb/f/f4/Neckarfront_T%C3%BCbingen_Mai_2017.jpg/775px-Neckarfront_T%C3%BCbingen_Mai_2017.jpg

# Creamos el directorio para los archivos de salida
!mkdir /content/output

# Cargo Librerias necesarias - OK

from keras.preprocessing.image import load_img, save_img, img_to_array
import numpy as np
import time
from scipy.optimize import fmin_l_bfgs_b
import argparse
from keras.applications import vgg19
from keras import backend as K
from pathlib import Path

# Version Tensorflow última - OK

import tensorflow as tf
print(tf.__version__)
tf.compat.v1.disable_eager_execution()

# Definimos las imagenes que vamos a utilizar, y el directorio de salida - OK

base_image_path = Path("/content/775px-Neckarfront_Tübingen_Mai_2017.jpg")
style_reference_image_path = Path("/content/La_noche_estrellada1.jpg")
result_prefix = Path("/content/output")
iterations = 100

# Una prueba de visualizacion -OK

import matplotlib.image as mpimg
import matplotlib.pyplot as plt

fig, (ax1, ax2) = plt.subplots(1, 2)
ax1.set_title("content image\n" + str(base_image_path))
img = mpimg.imread(base_image_path)
imgplot = ax1.imshow(img)
     
# ax2.title(style_reference_image_path)
ax2.set_title("style image\n" + str(style_reference_image_path))
img = mpimg.imread(style_reference_image_path)
imgplot = ax2.imshow(img)
plt.show()

"""# 1) En base a lo visto en el paper ¿Qué significan los parámetros definidos en la siguiente celda?

Respuesta: 
La funcion a minimizar para la generacion de la imagen es:



$\mathit{L}_{total}(\vec{p},\vec{a},\vec{x}) = α  L_{content}(\vec{p},\vec{x}) + β L_{style}(\vec{a},\vec{x})$

(Ver paper seccion)

Donde:

$\vec{p}$: Imagen original (**photograph**) a la cual se aplicara el estilo ($\vec{a}$)

$\vec{a}$: Imagen original (**artwork**) del estilo a aplicar a $\vec{p}$

$\vec{x}$: Imagen generada

$\alpha$: peso de la reconstruccion de la imagen basado en el contenido de la misma (Content Reconstruction) 

$\beta$: peso de la reconstruccion del estilo de la imagen (Style Reconstruction)



$\alpha$ y $\beta$  permiten dar mas enfasis al contenido o al estilo en la imagen generada (ver Figura 3), el paper establece una relacion entre ellos $\alpha / \beta$ (dependiendo de $w_{l}$ )

**total_variation_weigh** es utilizado como un término de regularización dentro de la Loss total. (Ver paper seccion 3)

**style_weight** esta en relacion con el N°.de features.

En la segunda celda se realiza un resize de las imágenes con las mismas medidas.

"""

# Aqui manejo los pesos que le doy al Style y el Content:

total_variation_weight = 0.1 #0.5
style_weight = 10 #1
content_weight = 1 #10

# Definimos el tamaño de las imágenes a utilizar:

width, height = load_img(base_image_path).size
img_nrows = 400
img_ncols = int(width * img_nrows / height)

print('medida input:',width,'x',height)
print('medida resize  :',img_nrows,'x',img_ncols)
print("Image content:", base_image_path)
print("Image width  :", width)
print("Image height :", height)
print("Image nrows  :", img_nrows)
print("Image ncols  :", img_ncols)
i=img_to_array(load_img(base_image_path))
print("Image mean(R):", i[:,:,0].mean())
print("Image mean(G):", i[:,:,1].mean())
print("Image mean(B):", i[:,:,2].mean())
print()

"""# 2) Explicar qué hace la siguiente celda. En especial las últimas dos líneas de la función antes del return. ¿Por qué?

Ayuda: https://keras.io/applications/

Respuesta:  

Esta función está preparando la imágen de entrada para que sea aceptada por el modelo en cuenanto a los requerimientos de este.  
La dos ultimas lineas se refieren a:  

**np.expand**: agrega una dimención mas entendiendo que esto trabaja con batches de imagenes, por lo que necesita en un batch con la imagen, por lo que el shape será ahora (imagenes, alto, ancho, canales)  

**vgg19.preprocess_input** : prepara la imágen según lo requiera el modelo, en este caso VGG19. VGG19 adecua la imagen a las necesidades del modelo.

Preprocesamiento:
- RGB > BGR
- zero-centered with respect to the ImageNet dataset, without scaling

**REFERENCIAS**:
**np.expand_dims** (https://numpy.org/doc/stable/reference/generated/numpy.expand_dims.html)
    
    Expand the shape of an array.
    
    
**vgg19.preprocess_input** (https://www.tensorflow.org/api_docs/python/tf/keras/applications/vgg19/preprocess_input)
 
    Preprocesses a tensor or Numpy array encoding a batch of images. 

**RGB/BGR** (https://lifearoundkaur.wordpress.com/2015/08/04/difference-between-rgb-and-bgr/)

**RGB** stands for Red Green Blue. 

Most often, an RGB color is stored in a structure or unsigned integer with Blue occupying the least significant “area” (a byte in 32-bit and 24-bit formats), Green the second least, and Red the third least.

**BGR** is the same, except the order of areas is reversed. 

"""

# Cargo imagen de un archivo y convierto a array:

def preprocess_image(image_path):
    img = load_img(image_path, target_size=(img_nrows, img_ncols))
    img = img_to_array(img)
    img = np.expand_dims(img, axis=0)
    img = vgg19.preprocess_input(img)
    return img

img = load_img(base_image_path, target_size=(img_nrows, img_ncols))
img = img_to_array(img)
img.shape

img = load_img(base_image_path, target_size=(img_nrows, img_ncols))

img

img = np.expand_dims(img, axis=0)
img.shape

"""# 3) Habiendo comprendido lo que hace la celda anterior, explique de manera muy concisa qué hace la siguiente celda. ¿Qué relación tiene con la celda anterior?

Respuesta:

**deprocess_Image** : Realiza el proceso inverso anterior. Se acomoda como imagen de 3 canales.  A cada uno de los canales le incrementa cada pixel en un valor predeterminado quitando los valores "0".  

Luego, intercambia de lugares los canales R con G para que sea una imagen en formato RGB (toma valores entre 0-255).


**REFERENCIAS**:
 
Ref: https://stackoverflow.com/questions/55987302/reversing-the-image-preprocessing-of-vgg-in-keras-to-return-original-image
"""

def deprocess_image(x):
    x = x.reshape((img_nrows, img_ncols, 3))
    # Remove zero-center by mean pixel
    x[:, :, 0] += 103.939
    x[:, :, 1] += 116.779
    x[:, :, 2] += 123.68
    # 'BGR'->'RGB'
    x = x[:, :, ::-1]
    x = np.clip(x, 0, 255).astype('uint8')
    
    return x

width, height,img_nrows,img_ncols

# get tensor representations of our images
# K.variable convierte un numpy array en un tensor, para 
base_image = K.variable(preprocess_image(base_image_path))
style_reference_image = K.variable(preprocess_image(style_reference_image_path))

combination_image = K.placeholder((1, img_nrows, img_ncols, 3))

"""Aclaración:

La siguiente celda sirve para procesar las tres imagenes (contenido, estilo y salida) en un solo batch.
"""

# combine the 3 images into a single Keras tensor

input_tensor = K.concatenate([base_image,
                              style_reference_image,
                              combination_image], axis=0)

# build the VGG19 network with our 3 images as input
# the model will be loaded with pre-trained ImageNet weights
model = vgg19.VGG19(input_tensor=input_tensor,
                    weights='imagenet', include_top=False)
print('Model loaded.')

# get the symbolic outputs of each "key" layer (we gave them unique names).
outputs_dict = dict([(layer.name, layer.output) for layer in model.layers])
model.summary()

"""# 4) En la siguientes celdas:

- ¿Qué es la matriz de Gram?¿Para qué se usa?

**Gram**: es la matriz de estilo (correlación entre estilos). Se define la matriz de Gram para un conjunto de vectores  v1 ,  v2 ,..., vn , tal que cada valor se calcula con el producto interno.

Se utiliza $G_{ij}$ para comparar cuan similar es $v_i$ con $v_j$.

**REFERENCIAS**:

**Gramian matrix** (https://en.wikipedia.org/wiki/Gramian_matrix)

En el paper referenciado, la representacion del estilo de la imagen (Style Representation) se calcula haciendo correlacion de la salida de los filtros aplicados en cada capa de la CNN.

Cada feature map en las diferentes capa contiene informacion capturada del estilo de la imagen, la matriz de Gram identificaria cuan similares son estos features 

El estilo se define utilizando features maps de mas una capa (paper: conv1_1, conv2_1, conv3_1, conv4_1, conv5_1)

Esta similitud (correlacion) se calcula utilizando la matriz de Gram para cada capa:  **$G^{l}  \in  \Re^{N_{l} x N_{l}}  $**,   siendo $G_{ij}^{l}$ el producto interno los feature maps

El calculo de la matriz de Gram se realiza haciendo un flatten y luego el producto interno.


- ¿Por qué se permutan las dimensiones de x?

**permute_dimensions**: al igual que *np.transpose()* y tendrá features "desenrrollados" (flatten)
"""

def gram_matrix(x):
    features = K.batch_flatten(K.permute_dimensions(x, (2, 0, 1)))
    gram = K.dot(features, K.transpose(features))
    return gram

"""# 5) Losses:

Explicar qué mide cada una de las losses en las siguientes tres celdas.

Rta:

**style_Loss**: Es la suma de distancias L2 entre las matrices Gram de las representaciones de la imagen base y la imagen de referencia de estilo, extraídas de diferentes capas de un convnet. Se captura información de color y textura a diferentes escalas espaciales, teniendo en cuenta la profundidad de cada capa.  

#### style_loss () ($L_{style}$)

**content_Loss**: Es una distancia L2 entre las características de la imagen base y las características de la imagen combinada, manteniendo la imagen generada lo mas parecida a la original.  

#### content_loss() ($L_{content}$)

**total_Variation_loss**: Continuidad espacial local entre los píxeles de la imagen combinada, brindando "coherencia visual".

#### total_variation_loss() ($L_{total\_variation\_loss}$)

"The total variation loss imposes local spatial continuity between the pixels of the combination image, giving it visual coherence."


**REFERENCIAS**:

https://arxiv.org/pdf/1508.06576.pdf (paper pg.10-11)

https://keras.io/examples/generative/neural_style_transfer/

https://www.tensorflow.org/tutorials/generative/style_transfer#total_variation_loss

"""

def style_loss(style, combination):
    assert K.ndim(style) == 3
    assert K.ndim(combination) == 3
    S = gram_matrix(style)
    C = gram_matrix(combination)
    channels = 3
    size = img_nrows * img_ncols
    return K.sum(K.square(S - C)) / (4.0 * (channels ** 2) * (size ** 2))

def content_loss(base, combination):
    return K.sum(K.square(combination - base))

def total_variation_loss(x):
    assert K.ndim(x) == 4
    a = K.square(
        x[:, :img_nrows - 1, :img_ncols - 1, :] - x[:, 1:, :img_ncols - 1, :])
    b = K.square(
        x[:, :img_nrows - 1, :img_ncols - 1, :] - x[:, :img_nrows - 1, 1:, :])
    return K.sum(K.pow(a + b, 1.25))

# Armamos la loss total
loss = K.variable(0.0)
layer_features = outputs_dict['block5_conv2']
base_image_features = layer_features[0, :, :, :]
combination_features = layer_features[2, :, :, :]
loss = loss + content_weight * content_loss(base_image_features,
                                            combination_features)

feature_layers = ['block1_conv1', 'block2_conv1',
                  'block3_conv1', 'block4_conv1',
                  'block5_conv1']

# Referencia paper: pagina 3, Figure1:
# We reconstruct the input image from from layers 
# ‘conv1 1’ (a), ‘conv2 1’ (b), 
# ‘conv3 1’ (c), ‘conv4 1’ (d) 
# ‘conv5 1’ (e) 
# of the orig- inal VGG-Network

for layer_name in feature_layers:
    layer_features = outputs_dict[layer_name]
    style_reference_features = layer_features[1, :, :, :] 
    combination_features = layer_features[2, :, :, :]
    sl = style_loss(style_reference_features, combination_features)
    loss = loss + (style_weight / len(feature_layers)) * sl
loss = loss + total_variation_weight * total_variation_loss(combination_image)

grads = K.gradients(loss, combination_image)

outputs = [loss]
if isinstance(grads, (list, tuple)):
    outputs += grads
else:
    outputs.append(grads)

f_outputs = K.function([combination_image], outputs)

"""# 6) Explique el propósito de las siguientes tres celdas. ¿Qué hace la función fmin_l_bfgs_b? ¿En qué se diferencia con la implementación del paper? ¿Se puede utilizar alguna alternativa?

Respuesta:

El paper define la  **loss total** ($\mathit{L}_{total}= \alpha  L_{content} + \beta L_{style}$) y no especifica ningun optimizador para el calculo.

En esta notebook se emplea una función de optimización y aquí se emplea esta que toma la Loss total para minimizarla utilizando el algoritmo **L-BFGS-B** sobre la imágen generada.

**scipy.optimize.fmin_l_bfgs_b**: minimiza la loss durante las iteraciones utilizando el algoritmo **L-BFGS-B** 

ver : (https://scipy.org/)

**fmin_l_bfgs_b**: Optimizador para calculo de la loss y gradiente (*eval_loss_and_grads*)

Dado que se requiere minimizar una funcion, podriamos aplicar cualquier otro optimizador, por ejemplo:  SGD.

**REFERENCIAS**:

**fmin_l_bfgs_b**: 
(https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.fmin_l_bfgs_b.html)

ver:  https://keras.io/examples/generative/neural_style_transfer/
     

"""

def eval_loss_and_grads(x):
    x = x.reshape((1, img_nrows, img_ncols, 3))
    outs = f_outputs([x])
    loss_value = outs[0]
    if len(outs[1:]) == 1:
        grad_values = outs[1].flatten().astype('float64')
    else:
        grad_values = np.array(outs[1:]).flatten().astype('float64')
    return loss_value, grad_values

# this Evaluator class makes it possible
# to compute loss and gradients in one pass
# while retrieving them via two separate functions,
# "loss" and "grads". This is done because scipy.optimize
# requires separate functions for loss and gradients,
# but computing them separately would be inefficient.

class Evaluator(object):

    def __init__(self):
        self.loss_value = None
        self.grads_values = None

    def loss(self, x):
        assert self.loss_value is None
        loss_value, grad_values = eval_loss_and_grads(x)
        self.loss_value = loss_value
        self.grad_values = grad_values
        return self.loss_value

    def grads(self, x):
        assert self.loss_value is not None
        grad_values = np.copy(self.grad_values)
        self.loss_value = None
        self.grad_values = None
        return grad_values



"""# 7) Ejecute la siguiente celda y observe las imágenes de salida en cada iteración."""

evaluator = Evaluator()

# run scipy-based optimization (L-BFGS) over the pixels of the generated image
# so as to minimize the neural style loss
x = preprocess_image(base_image_path)

for i in range(iterations):
    print('Start of iteration', i)
    start_time = time.time()
    x, min_val, info = fmin_l_bfgs_b(evaluator.loss, x.flatten(),
                                     fprime=evaluator.grads, maxfun=20)
    print('Current loss value:', min_val)
    # save current generated image
    img = deprocess_image(x.copy())
    fname = result_prefix / ('output_at_iteration_%d.png' % i)
    save_img(fname, img)
    end_time = time.time()
    print('Image saved as', fname)
    print('Iteration %d completed in %ds' % (i, end_time - start_time))



"""# 8) Generar imágenes para distintas combinaciones de pesos de las losses. Explicar las diferencias. (Adjuntar las imágenes generadas como archivos separados.)

Respuesta:

Estuve revisando de referencia para pensar el análisis:

https://keras.io/examples/generative/neural_style_transfer/

Pude observar mas precisamente en el sector del "cielo" y el "sol"  se pierden algunos detalles del propio contenido del pintor y se gana razgos del estilo que afectan a la nueva fotografía. Es interesante tambien distinguir el detalle de resolución del style original en los marcos de las ventanas y lineas rectas para las figuras: 

La asignación con el peso del estilo en 10 veces superior al peso del contenido, generan cambios en crecimiento desde la primera a la última iteración (0:99). 

# 9) Cambiar las imágenes de contenido y estilo por unas elegidas por usted. Adjuntar el resultado.

Respuesta:

En esta sección decidí utilizar lo aprendido y las posibilidades de Style Trasnfer como herramienta generativa computacional, para generar nuevo arte. 
En primer lugar seleccioné para la prueba imagenes de base: fotografías blanco y negro propias de mi autoría bajo la técnica fotográfica "pinhole" (también conocida como fotografía estenopeica). Luego tome de referencia para hacer Style Transfer la Obra del reconocido artista y fotógrafo argentino Marcelo Cugliari quien usa la misma técnica y posee una obra similar. y de aquí obtuve resultados fotográficos nuevos pero que mantienen el estilo de ambos. En particular la escena predominan mis formas, pero en los cielos y en la composición de cada objeto en escena es donde se ve mayor aún la influencia del estilo aplicado.
Por otra parte quise realizar la misma experiencia pero en la segunda prueba utilicé imagenes de pinturas de dos reconocidos pintores en la historia del arte. Para el caso particular tome al pintor Berni y luego apliqué el estilo de luz y contorno de Caravaggio. La experiencia fue interesante al poder comparar los rostros humanos entre ambas obras.

**REFERENCIAS**:

**Marcelo Cugliari**:

https://sites.google.com/view/marcelocugliari/home
"""



"""**Ignacio Kalaydjian Martínez - reactor82@hotmail.com** """