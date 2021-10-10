#!/usr/bin/env python

import numpy
import rospy

from collision_checker_rtc.msg import CollisionArray

from std_msgs.msg import ColorRGBA
from geometry_msgs.msg import Point
from geometry_msgs.msg import Vector3
from visualization_msgs.msg import Marker
from visualization_msgs.msg import MarkerArray

import tf
from tf.transformations import *

listener = None
pub_marker = None
sub_collision = None

def callback(msg) :
    now = rospy.Time.now()
    markerArray = MarkerArray()
    for collision in msg.collisions:
        (trans,rot) = listener.lookupTransform(collision.direction21.header.frame_id, collision.point2.header.frame_id, rospy.Time(0))
        link2_pose = tf.transformations.compose_matrix(translate=trans,angles=tf.transformations.euler_from_quaternion(rot))
        scale, shear, angles, translation, persp = tf.transformations.decompose_matrix(link2_pose.dot(tf.transformations.compose_matrix(translate=[collision.point2.point.x,collision.point2.point.y,collision.point2.point.z])))

        p1 = Point(*(numpy.add(translation,numpy.multiply([collision.direction21.vector.x,collision.direction21.vector.y,collision.direction21.vector.z],collision.distance))))
        p2 = Point(*translation)

        sphere_color = ColorRGBA(0,1,0,0.5)
        line_width = 0.005
        line_length = collision.distance
        sphere_scale = 0.02
        # color changes between 0.145(green) -> 0.02(red), under 0.02, it always red
        if (line_length <= 0.145) :
            sphere_scale = 0.02
            if ( line_length <= 0.0002) :
                sphere_scale = 0.045
                sphere_color = ColorRGBA(1, 0, 1, 1) ## color is purple, if collide
            elif ( line_length < 0.02) :
                sphere_scale = 0.04
                sphere_color = ColorRGBA(1, 0, 0, 1) ## color is red
            else:
                ratio = 1.0 - (line_length - 0.02) * 8 # 0.0 (0.145) -> 1.0 ( 0.02)
                sphere_scale = 0.02 + ratio * 0.02      # 0.02       -> 0.04
                sphere_color = ColorRGBA(ratio, 1 - ratio,0,1) # green -> red

        marker = Marker()
        marker.header.frame_id = collision.direction21.header.frame_id
        marker.type = marker.LINE_LIST
        marker.action = marker.ADD
        marker.color = sphere_color
        marker.points = [p1, p2]
        marker.scale.x = line_width
        marker.pose.orientation.w = 1.0
        markerArray.markers.append(marker)

        marker = Marker()
        marker.header.frame_id = collision.point1.header.frame_id
        marker.type = marker.SPHERE
        marker.action = marker.ADD
        marker.scale = Vector3(sphere_scale, sphere_scale, sphere_scale)
        marker.color = sphere_color
        marker.pose.orientation.w = 1.0
        marker.pose.position = collision.point1.point
        markerArray.markers.append(marker)

        marker = Marker()
        marker.header.frame_id = collision.point2.header.frame_id
        marker.type = marker.SPHERE
        marker.action = marker.ADD
        marker.scale = Vector3(sphere_scale, sphere_scale, sphere_scale)
        marker.color = sphere_color
        marker.pose.orientation.w = 1.0
        marker.pose.position = collision.point2.point
        markerArray.markers.append(marker)


    id = 0
    for m in markerArray.markers:
        m.lifetime = rospy.Duration(1.0)
        m.id = id
        id += 1

    pub_marker.publish(markerArray)


if __name__ == '__main__':
    rospy.init_node("collision_visualizer")

    listener = tf.TransformListener()
    pub_marker = rospy.Publisher('~marker', MarkerArray, queue_size=1)
    sub_collision = rospy.Subscriber("~collision", CollisionArray, callback)

    rospy.spin()