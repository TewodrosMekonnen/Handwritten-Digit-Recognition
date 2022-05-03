from streamlit_drawable_canvas import st_canvas
import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
import torch
import cv2
import torchvision

st.write('# Handwritten Digit Recognition')
st.write('## Using a MNIST and NN `PyTorch` model')

Network = torch.load('model_torch_MNIST_plus_CNN_98_5_streamlit.chk')

st.write('### Draw a digit in 0-9 in the box below')
# Specify canvas parameters in application
stroke_width = st.sidebar.slider("Stroke width: ", 1, 25, 9)

realtime_update = st.sidebar.checkbox("Update in realtime", True)

# Create a canvas component
canvas_result = st_canvas(
    fill_color="rgba(255, 165, 0, 0.3)",  # Fixed fill color with some opacity
    stroke_width=stroke_width,
    stroke_color='#FFFFFF',
    background_color='#000000',
    # background_image=Image.open(bg_image) if bg_image else None,
    update_streamlit=realtime_update,
    height=200,
    width=200,
    drawing_mode='freedraw',
    key="canvas",
)

# Do something interesting with the image data and paths
if canvas_result.image_data is not None:
    # st.write('### Image being used as input')
    # st.image(canvas_result.image_data)
    # st.write(type(canvas_result.image_data))
    # st.write(canvas_result.image_data.shape)
    # st.write(canvas_result.image_data)
    # im = Image.fromarray(canvas_result.image_data.astype('uint8'), mode="RGBA")
    # im.save("user_input.png", "PNG")

    # Get the numpy array (4-channel RGBA 100,100,4)
    input_numpy_array = np.array(canvas_result.image_data)

    # Get the RGBA PIL image
    input_image = Image.fromarray(input_numpy_array.astype('uint8'), 'RGBA')
    input_image.save('user_input.png')

    # Convert it to grayscale
    input_image_gs = input_image.convert('L')
    input_image_gs_np = np.asarray(input_image_gs.getdata()).reshape(200, 200)
    # st.write('### Image as a grayscale Numpy array')
    # st.write(input_image_gs_np)

    # Create a temporary image for opencv to read it
    input_image_gs.save('temp_for_cv2.jpg')
    image = cv2.imread('temp_for_cv2.jpg', 0)
    # Start creating a bounding box
    height, width = image.shape
    x, y, w, h = cv2.boundingRect(image)

    # Create new blank image and shift ROI to new coordinates
    ROI = image[y:y + h, x:x + w]
    mask = np.zeros([ROI.shape[0] + 10, ROI.shape[1] + 10])
    width, height = mask.shape
    #     print(ROI.shape)
    #     print(mask.shape)
    x = width // 2 - ROI.shape[0] // 2
    y = height // 2 - ROI.shape[1] // 2
    #     print(x,y)
    mask[y:y + h, x:x + w] = ROI
    #     print(mask)
    # Check if centering/masking was successful
    #     plt.imshow(mask, cmap='viridis')
    output_image = Image.fromarray(mask)  # mask has values in [0-255] as expected
    # Now we need to resize, but it causes problems with default arguments as it changes the range of pixel values to be negative or positive
    # compressed_output_image = output_image.resize((22,22))
    # Therefore, we use the following:
    compressed_output_image = output_image.resize((22, 22),
                                                  Image.BILINEAR)  # PIL.Image.NEAREST or PIL.Image.BILINEAR also performs good

    convert_tensor = torchvision.transforms.ToTensor()
    tensor_image = convert_tensor(compressed_output_image)
    # Another problem we face is that in the above ToTensor() command, we should have gotten a normalized tensor with pixel values in [0,1]
    # But somehow it doesn't happen. Therefore, we need to normalize manually
    tensor_image = tensor_image / 255.
    # Padding
    tensor_image = torch.nn.functional.pad(tensor_image, (3, 3, 3, 3), "constant", 0)
    # Normalization shoudl be done after padding i guess
    convert_tensor = torchvision.transforms.Normalize((0.1281), (0.3043))  # Mean and std of MNIST_plus
    tensor_image = convert_tensor(tensor_image)
    # st.write(tensor_image.shape)
    # Shape of tensor image is (1,28,28)

    # st.write('### Processing steps:')
    # st.write('1. Find the bounding box of the digit blob and use that.')
    # st.write('2. Convert it to size 22x22.')
    # st.write('3. Pad the image with 3 pixels on all the sides to get a 28x28 image.')
    # st.write('4. Normalize the image to have pixel values between 0 and 1.')
    # st.write('5. Standardize the image using the mean and standard deviation of the MNIST_plus dataset.')

    # The following gives noisy image because the values are from -1 to 1, which is not a proper image format
    im = Image.fromarray(tensor_image.detach().cpu().numpy().reshape(28, 28), mode='L')
    im.save("processed_tensor.png", "PNG")
    # So we use matplotlib to save it instead
    plt.imsave('processed_tensor.png', tensor_image.detach().cpu().numpy().reshape(28, 28), cmap='gray')

    # st.write('### Processed image')
    # st.image('processed_tensor.png')
    # st.write(tensor_image.detach().cpu().numpy().reshape(28,28))

    device = 'cpu'
    ### Compute the predictions
    with torch.no_grad():
        # input image for network should be (1,1,28,28)
        output0 = Network(torch.unsqueeze(tensor_image, dim=0).to(device=device))
        # Need to apply Softmax here to get probabilities
        m = torch.nn.Softmax(dim=1)
        output0 = m(output0)
        # st.write(output0)
        certainty, output = torch.max(output0[0], 0)
        certainty = certainty.clone().cpu().item()
        output = output.clone().cpu().item()
        certainty1, output1 = torch.topk(output0[0], 3)
        certainty1 = certainty1.clone().cpu()  # .item()
        output1 = output1.clone().cpu()  # .item()
    #     print(certainty)
    st.write('### Prediction')
    st.write('### ' + str(output))

    st.write('## Breakdown of the prediction process:')

    st.write('### Image being used as input')
    st.image(canvas_result.image_data)

    st.write('### Image as a grayscale Numpy array')
    st.write(input_image_gs_np)

    st.write('### Processing steps:')
    st.write('1. Find the bounding box of the digit blob and use that.')
    st.write('2. Convert it to size 22x22.')
    st.write('3. Pad the image with 3 pixels on all the sides to get a 28x28 image.')
    st.write('4. Normalize the image to have pixel values between 0 and 1.')
    st.write('5. Standardize the image using the mean and standard deviation of the MNIST_plus training dataset.')

    st.write('### Processed image')
    st.image('processed_tensor.png')

    st.write('### Prediction')
    st.write(str(output))
    st.write('### Certainty')
    st.write(str(certainty1[0].item() * 100) + '%')
    st.write('### Top 3 candidates')
    st.write(str(output1))
    st.write('### Certainties')
    st.write(str(certainty1 * 100))