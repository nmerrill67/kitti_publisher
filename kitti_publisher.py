#!/usr/bin/env python
from __future__ import print_function
import rospy
from geometry_msgs.msg import PointStamped
from sensor_msgs.msg import Image
from cv2 import imread # opencv
from os.path import join
from click import progressbar
from cv_bridge import CvBridge, CvBridgeError

def kitti_publisher(vo_fn="", im_dir="", rate=1.0):
	rospy.init_node('kitti_publisher', anonymous=True)
	rate = rospy.Rate(10.0 * rate) # 20 * rate hz

	if vo_fn != "":
		point_pub = rospy.Publisher('/kitti/position', PointStamped, queue_size=100)
	if im_dir != "":
		imL_pub = rospy.Publisher('/kitti/stereo/left', Image, queue_size=10)
		imR_pub = rospy.Publisher('/kitti/stereo/right', Image, queue_size=10)
		
	cvb = CvBridge()
	i = 0
	with open(vo_fn, 'r') as vo_f:
		with progressbar(vo_f.readlines(), label="Publishing KITTI Data") as bar:
			for line in bar:
				if not rospy.is_shutdown():
					if len(line) != 0 and line[0] != "#": # skip comments and empty line at the end
						line_split = line.split()
						frame_id = str(i)
						i += 1
						if vo_fn != "":
							point = PointStamped()
							point.header.frame_id = frame_id
							point.point.x = float(line_split[3])
							point.point.y = float(line_split[7])
							point.point.z = float(line_split[11])
							point_pub.publish(point)

						if im_dir != "":
							fl_nm = str(i).zfill(6) + ".png"
							imL = imread(join(im_dir, "image_0/"+ fl_nm))
							imR = imread(join(im_dir, "image_1/"+ fl_nm))
							if imL is None or imR is None:
								break
							msgL = cvb.cv2_to_imgmsg(imL, "bgr8")
							msgL.header.frame_id = frame_id
							msgR = cvb.cv2_to_imgmsg(imR, "bgr8")
							msgR.header.frame_id = frame_id
							imL_pub.publish(msgL)
							imR_pub.publish(msgR)					
									
						rate.sleep()

if __name__ == '__main__':

	from argparse import ArgumentParser as Parser

	parser = Parser()
	parser.add_argument("-s", "--sequence", dest="seq", nargs='?', help="Sequence number to publish. Default is 0", default="0")
	parser.add_argument("-r", "--rate", dest="rate", nargs='?', help="The rate at which to play back the data", default=1.0, type=float)
	args = parser.parse_args()	
	
	vo_fn = "dataset/poses/" + args.seq.zfill(2) + ".txt"
	im_dir = "dataset/sequences/" + args.seq.zfill(2) 

	try:
		kitti_publisher(vo_fn, im_dir, args.rate)
	except rospy.ROSInterruptException:
		pass
