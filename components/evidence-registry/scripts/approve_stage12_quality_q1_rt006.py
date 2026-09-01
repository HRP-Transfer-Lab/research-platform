import prepare_stage12_review_surface_packets as prep
from stage12_quality_q1_rt006_batch import install

install(prep)

import approve_stage12_review_surface_packet as approval

if __name__ == "__main__":
    raise SystemExit(approval.main())
