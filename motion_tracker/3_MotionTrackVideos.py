from __init__ import *


def predict(xs, ys, ts=None, num_frames=30):
    # to do: implement Kalman filter to predict points
    no_nans = np.isnan(xs) == False
    new_x = xs[no_nans][-1]
    new_y = ys[no_nans][-1]

    return new_x, new_y


def track_video(vid, num_points=3, movement_threshold=90, make_video=True,
                pointer_length=3):
    back = vid[::100].mean(0).astype(int)
    if make_video:
        new_vid = np.zeros(
            (vid.shape[0], vid.shape[1], vid.shape[2], 3), dtype='uint8')
    else:
        new_vid = None
    num_frames, height, width = vid.shape
    coords = np.zeros([num_frames, num_points, 2])
    coords[:] = np.nan

    shape = list(vid.shape[1:]) + [3]
    clusterer = cluster.KMeans(num_points)

    for num, frame in enumerate(vid):
        diff = abs(frame.astype(int) - back).astype('uint8')
        thresh = diff > movement_threshold
        ys, xs = np.where(thresh)
        arr = np.array([xs, ys]).T
        try:
            clusterer.fit(arr)
            labels = clusterer.labels_
            points = clusterer.cluster_centers_
            coords[num] = points
            future_points = []
            for path in coords.transpose(1, 2, 0):
                px, py = path
                future_points += [predict(px, py)]
            clusterer.init = np.array(future_points)
            clusterer.n_init = 1
        except:
            points = np.repeat(np.nan, num_points)

        if make_video:
            new_vid[num] = np.repeat(frame[..., np.newaxis], 3, axis=-1)
            if np.isnan(points).sum() == num_points:
                pass
            else:
                for label, color in zip(sorted(set(labels)), colors):
                    i = labels == label
                    x, y = int(
                        np.round(xs[i].mean())), int(np.round(ys[i].mean()))
                    new_vid[num, y - pointer_length:y + pointer_length,
                            x - pointer_length: x + pointer_length] = 255 * np.array(
                                plt.cm.colors.to_rgb(color))

        print_progress(num, num_frames)

    coords = np.array(coords)
    return coords, new_vid


class VideoTracker():
    def __init__(self, num_points=1, make_video=True, video_files=None,
                 tracks_folder='tracking_data', movement_threshold=90):
        self.num_points = num_points
        self.movement_threshold = movement_threshold
        self.make_video = make_video
        self.app = QApplication.instance()
        if self.app is None:
            self.app = QApplication([])
        # grab the video files
        if video_files is None:
            print("Select the video files you want to motion track:")
            file_UI = FileSelector()
            file_UI.close()
            self.video_files = file_UI.files
        else:
            self.video_files = video_files
        # figure out the parent directory
        self.folder = os.path.dirname(self.video_files[0])
        os.chdir(self.folder)
        # find/make tracks_folder
        self.tracks_folder = os.path.join(self.folder, tracks_folder)
        if os.path.isdir(self.tracks_folder) is False:
            os.mkdir(self.tracks_folder)

    def track_files(self):
        for fn in self.video_files:
            # make a new filename for the tracking data
            print(f"Tracking file {fn}:")
            ftype = "." + fn.split(".")[-1]
            new_fn = os.path.basename(fn)
            new_fn = new_fn.replace(ftype, "_track_data.npy")
            new_fn = os.path.join(self.tracks_folder, new_fn)
            vid = np.squeeze(io.vread(fn, as_grey=True))
            coords, new_vid = track_video(
                vid, num_points=self.num_points,
                make_video=self.make_video,
                movement_threshold=self.movement_threshold)
            np.save(new_fn, coords)

            if self.make_video:
                vid_fn = new_fn.replace("_data.npy", "_video.mp4")
                new_fn = os.path.join(self.tracks_folder, new_fn)
                io.vwrite(vid_fn, new_vid)
                print(f"Tracking video saved at {vid_fn}")


if __name__ == "__main__":
    num_points = int(input("How many objects are moving, maximum? "))
    make_video = input(
        "Do you want to save a video of the tracking data? Type 1 for "
        "yes and 0 for no: ")
    while make_video not in ["0", "1"]:
        make_video = input(
            "The response must be a 0 or a 1")
    make_video = bool(int(make_video))

    video_tracker = VideoTracker(
        num_points=num_points, movement_threshold=90, make_video=make_video)
    video_tracker.track_files()