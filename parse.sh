SRC_DIR="data"
DEST_DIR="data/events"


mkdir -p "$DEST_DIR"

for dir in "$SRC_DIR"/*eve; do
#if folders end in "-eve"
    if [ -d "$dir" ]; then 
        mv "$dir" "$DEST_DIR"
    fi
done

SRC_DIR="data"
DEST_DIR="data/box_scores"


mkdir -p "$DEST_DIR"

for dir in "$SRC_DIR"/*box; do
#if folders end in "-eve"
    if [ -d "$dir" ]; then 
        mv "$dir" "$DEST_DIR"
    fi
done

for file in {1910..2023}
do
  echo "Processing $year"
  cwevent -n -f 0-96 -y $year $year*.EV* > events_$year.csv
  cwgame -n -f 0-83 $year*.EV* > games_$year.csv
  cwroster $year*.ROS > rosters_$year.csv
done

