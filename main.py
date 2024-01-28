from GeoMixTrail import DFTrack, AnimationTrack

track = DFTrack("points copy.csv", point_distance_meters=200)
track.set_colors("Speed")
animationTrack = AnimationTrack(track, width=768, height=768)
animationTrack.make_video("animation.mp4", duration=10)