if __name__ in {"__main__", "__mp_main__"}:
    from hydranav import init_parser, GCS

    parser = init_parser()
    args = parser.parse_args()
    gcs = GCS(args)
    gcs.run()
