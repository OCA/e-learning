changelog:
	@oca-towncrier --repo=e-learning --addon-dir=elearning_data --addon-dir=elearning_shuffle_slide_answer --addon-dir=elearning_url_slide_slide --no-commit

towncrier:
	@bash create_fragment.sh