import prepare_stage12_review_surface_packets as prep
from stage12_quality_q1_rt006_batch import install

install(prep)

import validate_stage12_review_surface_packet as validator

if __name__ == "__main__":
    raise SystemExit(validator.main())
