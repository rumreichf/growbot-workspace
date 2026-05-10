self.tf_buffer = Buffer()
self.tf_listener = TransformListener(
    self.tf_buffer,
    self
)

self.save_path = os.path.expanduser(
    "~/ros2_ws/plants.json"
)
