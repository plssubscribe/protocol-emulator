# Remove stale signal/clock wires before regenerating guides after diode repair.
# OpenDB destroyRoutes preserves supply, special and abutment-connected routes.
source $::env(SCRIPTS_DIR)/openroad/common/io.tcl
read_current_odb
$::block destroyRoutes
puts "\[INFO\] Cleared normal signal routes; retained cells, nets and special power routing."
write_views
