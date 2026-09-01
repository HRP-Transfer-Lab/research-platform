import prepare_stage12_review_surface_packets as prep
from stage12_quality_q1_rt014_batch import install

install(prep)

if __name__ == "__main__":
    raise SystemExit(prep.main())
