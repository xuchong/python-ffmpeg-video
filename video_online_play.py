import cv2
import urllib
import datetime
import numpy as np
import subprocess as sp

THREAD_NUM=4

'''
using opencv or urllib...   not work
'''
def method1():

    # cap = cv2.VideoCapture('http://localhost/1.ts')
    # print cap.isOpened()
    # couldn't open

    # can be use for mpeg
    stream=urllib.urlopen('http://localhost/1.mpeg')
    bytes=''
    while True:
        bytes+=stream.read(1024)
        print bytes
        a = bytes.find('\xff\xd8')
        b = bytes.find('\xff\xd9')
        if a!=-1 and b!=-1:
            jpg = bytes[a:b+2]
            bytes= bytes[b+2:]
            i = cv2.imdecode(np.fromstring(jpg, dtype=np.uint8),cv2.IMREAD_COLOR)
            cv2.imshow('i',i)
            if cv2.waitKey(1) ==27:
                exit(0)

'''
using ffmpeg:   get video to image from url. 
commands:  ffmpeg -i "http://localhost/1.ts" -r 1 -f image2 %05d.jpg   
-r  1:  1 frame each second
-f image2
'''
def get_video_info(fileloc) :
    command = ['ffprobe',
               '-v', 'fatal',
               '-show_entries', 'stream=width,height,r_frame_rate,duration',
               '-of', 'default=noprint_wrappers=1:nokey=1',
               fileloc, '-sexagesimal']
    ffmpeg = sp.Popen(command, stderr=sp.PIPE ,stdout = sp.PIPE )
    out, err = ffmpeg.communicate()
    if(err) : print(err)
    out = out.split('\n')
    return {'file' : fileloc,
            'width': int(out[0]),
            'height' : int(out[1]),
            'fps': float(out[2].split('/')[0])/float(out[2].split('/')[1]),
            'duration' : out[3] }

def get_video_frame_count(fileloc) : # This function is spearated since it is slow.
    command = ['ffprobe',
               '-v', 'fatal',
               '-count_frames',
               '-show_entries', 'stream=nb_read_frames',
               '-of', 'default=noprint_wrappers=1:nokey=1',
               fileloc, '-sexagesimal']
    ffmpeg = sp.Popen(command, stderr=sp.PIPE ,stdout = sp.PIPE )
    out, err = ffmpeg.communicate()
    if(err) : print(err)
    out = out.split('\n')
    return {'file' : fileloc,
            'frames' : out[0]}

def read_frame(fileloc,start_frame,fps,num_frame,t_w,t_h,persecond_num=1) :
    command = ['ffmpeg',
               '-loglevel', 'fatal',
               '-ss', str(datetime.timedelta(seconds=start_frame/fps)),
               '-i', fileloc,
               '-threads', str(THREAD_NUM),
               '-vf', 'scale=%d:%d'%(t_w,t_h),
               '-vframes', str(num_frame),
               '-f', 'image2pipe',
               '-pix_fmt', 'rgb24',
               '-r',str(persecond_num),
               '-vcodec', 'rawvideo', '-']
    ffmpeg = sp.Popen(command, stderr=sp.PIPE ,stdout = sp.PIPE,bufsize=10**9)
    out, err = ffmpeg.communicate()
    if(err) : print('error',err); return None;
    video = np.fromstring(out, dtype='uint8').reshape(-1,t_h,t_w,3)
    return video

'''easy version: image size fixed 360x420'''
def method2(fileloc):
    FFMPEG_BIN = "ffmpeg"
    command = [FFMPEG_BIN,
               '-i', fileloc,
               '-f', 'image2pipe',
               '-pix_fmt', 'rgb24',
               '-r','1',
               '-vcodec', 'rawvideo', '-']
    pipe = sp.Popen(command, stdout=sp.PIPE, bufsize=10 ** 9)
    # read 420*360*3 bytes (= 1 frame)
    raw_image = pipe.stdout.read(420*360*3)
    # transform the byte read into a numpy array
    image = np.fromstring(raw_image, dtype='uint8')
    image = image.reshape((360, 420, 3))
    # throw away the data in the pipe's buffer.
    pipe.stdout.flush()
    cv2.imshow("mv", image)
    cv2.waitKey(0)


if __name__=='__main__':
    video_url = 'http://localhost/1.ts'
    video_info = get_video_info(video_url)
    video_count = get_video_frame_count(video_url)

    print video_info,video_count

    video = read_frame(video_url,0,int(video_info['fps']),int(video_count['frames']),int(video_info['width']),int(video_info['height']))
    # show video
    for i in range(video.shape[0]):
        #change RGB to BGR
        cv2.imshow("video",video[i][:,:,::-1])
        cv2.waitKey(0)
