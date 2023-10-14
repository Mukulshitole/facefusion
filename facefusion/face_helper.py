from typing import Tuple, Dict

import cv2
import numpy

from facefusion.typing import Face, Frame, Matrix, Template

TEMPLATES : Dict[str, numpy.array] =\
{
	'arface': numpy.array(
	[
		[ 38.2946, 51.6963 ],
		[ 73.5318, 51.5014 ],
		[ 56.0252, 71.7366 ],
		[ 41.5493, 92.3655 ],
		[ 70.7299, 92.2041 ]
	]),
	'ffhq': numpy.array(
	[
		[ 192.98138, 239.94708 ],
		[ 318.90277, 240.1936 ],
		[ 256.63416, 314.01935 ],
		[ 201.26117, 371.41043 ],
		[ 313.08905, 371.15118 ]
	])
}


def warp_face(target_face : Face, temp_frame : Frame, template : Template) -> Tuple[Frame, Matrix]:
	affine_matrix = cv2.estimateAffinePartial2D(target_face.kps, TEMPLATES[template], method = cv2.LMEDS)[0]
	crop_frame = cv2.warpAffine(temp_frame, affine_matrix, (512, 512))
	return crop_frame, affine_matrix


def paste_back(temp_frame : Frame, crop_frame : Frame, affine_matrix : Matrix) -> Frame:
	inverse_affine_matrix = cv2.invertAffineTransform(affine_matrix)
	temp_frame_height, temp_frame_width = temp_frame.shape[0:2]
	crop_frame_height, crop_frame_width = crop_frame.shape[0:2]
	inverse_crop_frame = cv2.warpAffine(crop_frame, inverse_affine_matrix, (temp_frame_width, temp_frame_height))
	inverse_mask = numpy.ones((crop_frame_height, crop_frame_width, 3), dtype = numpy.float32)
	inverse_mask_frame = cv2.warpAffine(inverse_mask, inverse_affine_matrix, (temp_frame_width, temp_frame_height))
	inverse_mask_frame = cv2.erode(inverse_mask_frame, numpy.ones((2, 2)))
	inverse_mask_border = inverse_mask_frame * inverse_crop_frame
	inverse_mask_area = numpy.sum(inverse_mask_frame) // 3
	inverse_mask_edge = int(inverse_mask_area ** 0.5) // 20
	inverse_mask_radius = inverse_mask_edge * 2
	inverse_mask_center = cv2.erode(inverse_mask_frame, numpy.ones((inverse_mask_radius, inverse_mask_radius)))
	inverse_mask_blur_size = inverse_mask_edge * 2 + 1
	inverse_mask_blur_area = cv2.GaussianBlur(inverse_mask_center, (inverse_mask_blur_size, inverse_mask_blur_size), 0)
	temp_frame = inverse_mask_blur_area * inverse_mask_border + (1 - inverse_mask_blur_area) * temp_frame
	temp_frame = temp_frame.clip(0, 255).astype(numpy.uint8)
	return temp_frame