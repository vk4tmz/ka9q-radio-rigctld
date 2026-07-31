#!/usr/bin/env bash

###############################################################################
# virtual_vfo_streamer.sh
#
# Combined controller for:
#   - virtual PulseAudio/PipeWire sinks
#   - KA9Q VFO streamers
#
# Usage:
#   ./virtual_vfo_streamer.sh [-c|--config-dir DIR] list
#   ./virtual_vfo_streamer.sh [-c|--config-dir DIR] <GROUP_ID> start
#   ./virtual_vfo_streamer.sh [-c|--config-dir DIR] <GROUP_ID> stop
#   ./virtual_vfo_streamer.sh [-c|--config-dir DIR] <GROUP_ID> restart
#   ./virtual_vfo_streamer.sh [-c|--config-dir DIR] <GROUP_ID> status
#
# Examples:
#   ./virtual_vfo_streamer.sh list
#   ./virtual_vfo_streamer.sh hf_aprs start
#
###############################################################################

set -euo pipefail

###############################################################################
# GLOBALS and PATHS
###############################################################################

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

ORIGINAL_DIR="$(pwd)"

PROJECT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

if command -v ka9q-vfo-streamer >/dev/null 2>&1; then
    KA9Q_VFO_COMMAND=(ka9q-vfo-streamer)
else
    KA9Q_VFO_STREAMER="${PROJECT_DIR}/ka9q_vfo_streamer.py"
    KA9Q_VFO_COMMAND=(python "$KA9Q_VFO_STREAMER")
fi

DEFAULT_STREAMER_CFG_DIR="${HOME}/.config/ka9q-radio/vfo_streamer"

STREAMER_CFG_DIR="$DEFAULT_STREAMER_CFG_DIR"

GROUP_ID=""
GROUP_DIR=""
GROUP_CONFIG_FILE=""

LOG_DIR=""
PID_FILE=""
MODULE_FILE=""
LOCK_FILE=""
LOCK_HELD=0

ACTION=""
REMAINING_ARGS=()


###############################################################################
# LOCKING
###############################################################################

check_lock_requirements()
{
    command -v flock >/dev/null || {
        error "flock not found"
        exit 1
    }
}

acquire_lock()
{

    check_lock_requirements

    mkdir -p "$GROUP_DIR"

    exec 200>"$LOCK_FILE"

    if ! flock -n 200; then
        error "Another virtual_vfo_streamer instance is already running"
        error "GROUP_ID: ${GROUP_ID}"
        error "Lock: ${LOCK_FILE}"
        exit 1
    fi

    LOCK_HELD=1

    info "Lock acquired: ${LOCK_FILE}"
}

release_lock()
{
    if [[ $LOCK_HELD -eq 1 ]]; then
        flock -u 200 || true
        exec 200>&-
        LOCK_HELD=0
        info "Lock released"
    fi
}

###############################################################################
# LOGGING
###############################################################################

info()
{
    echo "[INFO ] $*"
}

warn()
{
    echo "[WARN ] $*" >&2
}

error()
{
    echo "[ERROR] $*" >&2
}


###############################################################################
# CLEANUP
###############################################################################

restore_cwd()
{
    if [[ $LOCK_HELD -eq 1 ]]; then
        release_lock
    fi

    cd "$ORIGINAL_DIR" 2>/dev/null || true
}

trap restore_cwd EXIT INT TERM


###############################################################################
# REQUIREMENTS
###############################################################################

check_runtime_requirements()
{
    command -v python >/dev/null || {
        error "python not found"
        exit 1
    }

    if [[ "${KA9Q_VFO_COMMAND[0]}" == "python" ]]; then
        [[ -f "${KA9Q_VFO_COMMAND[1]}" ]] || {
            error "KA9Q VFO streamer not found: ${KA9Q_VFO_COMMAND[1]}"
            exit 1
        }
    fi
}

check_audio_requirements()
{
    command -v pactl >/dev/null || {
        error "pactl not found"
        exit 1
    }
}

###############################################################################
# ARGUMENT HANDLING
###############################################################################

parse_global_options()
{
    while [[ $# -gt 0 ]]; do

        case "$1" in

            -c|--config-dir)

                if [[ $# -lt 2 ]]; then
                    error "Missing argument for $1"
                    exit 1
                fi

                if [[ -z "$2" ]]; then
                    error "Empty config directory"
                    exit 1
                fi

                if [[ ! -d "$2" ]]; then
                    error "Config directory does not exist: $2"
                    exit 1
                fi

                STREAMER_CFG_DIR="$(cd "$2" && pwd)"

                shift 2
                ;;

            --)

                shift
                break
                ;;

            *)

                break
                ;;

        esac

    done

    REMAINING_ARGS=("$@")
}

validate_group_id()
{
    if [[ ! "$GROUP_ID" =~ ^[a-zA-Z0-9_-]+$ ]]; then
        error "Invalid GROUP_ID: $GROUP_ID"
        error "Only letters, numbers, underscore and dash allowed"
        exit 1
    fi
}

validate_arguments()
{

    if [[ $# -lt 1 ]]; then
        error "Missing arguments"
        usage
        exit 1
    fi

    if [[ "${1,,}" == "list" ]]; then
        ACTION="list"
        return
    fi

    if [[ $# -lt 2 ]]; then
        error "Missing arguments"
        usage
        exit 1
    fi

    GROUP_ID="$1"
    ACTION="${2,,}"

    validate_group_id

    case "$ACTION" in
        start|stop|restart|status)
            ;;
        *)
            error "Invalid action: $ACTION"
            usage
            exit 1
            ;;
    esac


    GROUP_DIR="${STREAMER_CFG_DIR}/${GROUP_ID}"

    GROUP_CONFIG_FILE="${VFO_GROUP_CONFIG_FILE:-${GROUP_DIR}/${GROUP_ID}.conf}"

    LOG_DIR="${GROUP_DIR}/logs"

    PID_FILE="${GROUP_DIR}/vfo_pids.txt"

    MODULE_FILE="${GROUP_DIR}/virtual_card_module_ids"

    LOCK_FILE="${GROUP_DIR}/.group.lock"
}

###############################################################################
# CONFIGURATION
###############################################################################

validate_radio_channels()
{
    local count=0

    for channel in "${RADIO_CHANNELS[@]}"; do

        read -r VC FREQ_HZ MODE <<< "$channel"

        if [[ -z "$VC" || -z "$FREQ_HZ" || -z "$MODE" ]]; then
            error "Invalid RADIO_CHANNELS entry:"
            echo "  $channel"
            exit 1
        fi

        if ! [[ "$FREQ_HZ" =~ ^[0-9]+$ ]]; then
            error "Invalid frequency: $FREQ_HZ"
            exit 1
        fi

        if [[ ! "$VC" =~ ^[a-zA-Z0-9_-]+$ ]]; then
            error "Invalid VC: $VC"
            error "Only letters, numbers, underscore and dash allowed"
            exit 1
        fi

        count=$((count + 1))

    done

    if [[ $count -eq 0 ]]; then
        error "RADIO_CHANNELS is empty"
        exit 1
    fi
}

list_groups()
{
    if [[ ! -d "$STREAMER_CFG_DIR" ]]; then
        echo "No VFO streamer groups found"
        return
    fi

    find "$STREAMER_CFG_DIR" \
        -maxdepth 1 \
        -mindepth 1 \
        -type d \
        -printf "%f\n"
}

validate_group_config()
{
    if [[ -z "$GROUP_ID" ]]; then
        error "GROUP_ID is not set"
        exit 1
    fi

    if [[ ! -f "$GROUP_CONFIG_FILE" ]]; then
        error "Missing configuration file:"
        echo "  $GROUP_CONFIG_FILE"
        exit 1
    fi
}

validate_config()
{
    local required_vars=(
        HOST
        BASE_SSRC
        BASE_PORT
        RATE
        RADIO_CHANNELS
    )

    for var in "${required_vars[@]}"; do
        if [[ -z "${!var:-}" ]]; then
            error "Missing config variable: $var"
            exit 1
        fi
    done

    validate_radio_channels
    
}

load_config()
{
    validate_group_config

    mkdir -p "$GROUP_DIR"
    mkdir -p "$LOG_DIR"

    # shellcheck disable=SC1090
    source "$GROUP_CONFIG_FILE"

    validate_config
}


###############################################################################
# VIRTUAL CARD MANAGEMENT
###############################################################################

load_virtual_cards()
{
    info "Loading ${GROUP_ID} virtual sinks..."

    if [[ -f "$MODULE_FILE" ]]; then
        unload_virtual_cards
    fi

    local tmp_file="${MODULE_FILE}.tmp"

    rm -f "$tmp_file"
    > "$tmp_file"

    local load_failed=0

    for channel in "${RADIO_CHANNELS[@]}"; do

        read -r VC FREQ_HZ MODE <<< "$channel"

        local sink="vc_${GROUP_ID}_${VC}"

        info "Creating ${sink}"

        local module_id

        if ! module_id=$(pactl load-module module-null-sink \
            sink_name="$sink" \
            sink_properties="device.description=${GROUP_ID} VFO ${VC}"); then

            error "Failed loading ${sink}"
            load_failed=1
            break
        fi

        echo "${sink} ${FREQ_HZ} ${module_id}" >> "$tmp_file"

    done

    if ! mv "$tmp_file" "$MODULE_FILE"; then
        error "Failed writing module state file"
        rm -f "$tmp_file"
        return 1
    fi

    if [[ $load_failed -ne 0 ]]; then
        warn "One or more virtual sinks failed to load."
        
        return 1
    fi

    info "Virtual sinks loaded"
}


unload_virtual_cards()
{
    if [[ ! -f "$MODULE_FILE" ]]; then
        info "No virtual sink module file found"
        return
    fi

    if [[ ! -r "$MODULE_FILE" ]]; then
        error "Cannot read virtual sink module file: $MODULE_FILE"
        exit 1
    fi

    if [[ ! -s "$MODULE_FILE" ]]; then
        rm -f "$MODULE_FILE"
        info "Empty virtual sink module file removed"
        return
    fi

    info "Unloading ${GROUP_ID} virtual sinks..."

    while read -r SINK FREQ_HZ MODULE_ID; do

        [[ -z "$MODULE_ID" ]] && continue

        info "Removing ${SINK} (module ${MODULE_ID})"

        if ! pactl unload-module "$MODULE_ID"; then
            warn "Failed unloading module ${MODULE_ID}"
        fi

    done < "$MODULE_FILE"

    rm -f "$MODULE_FILE"

    info "Virtual sinks unloaded"
}

###############################################################################
# VFO STREAMER MANAGEMENT
###############################################################################

start_streamers()
{
    info "Starting ${GROUP_ID} streamers..."

    local tmp_file="${PID_FILE}.tmp"

    rm -f "$tmp_file"
    > "$tmp_file"

    local SSRC=$BASE_SSRC
    local PORT=$BASE_PORT

    local start_failed=0

    for channel in "${RADIO_CHANNELS[@]}"; do

        read -r VC FREQ_HZ MODE <<< "$channel"

        local SINK="vc_${GROUP_ID}_${VC}"

        local CURRENT_SSRC="$SSRC"
        local CURRENT_PORT="$PORT"

        local LOG_FILE="${LOG_DIR}/vfo_${VC}_${FREQ_HZ}.log"

        info "Starting ${SINK} ${FREQ_HZ}Hz"

        "${KA9Q_VFO_COMMAND[@]}" \
            "$HOST" \
            "$CURRENT_SSRC" \
            "$FREQ_HZ" \
            "$MODE" \
            -ar "$RATE" \
            -ad "$SINK" \
            --host localhost \
            --port "$CURRENT_PORT" \
            > "$LOG_FILE" 2>&1 &


        local PID=$!

        sleep 0.2

        if ! kill -0 "$PID" 2>/dev/null; then
            start_failed=1
            warn "Streamer failed to start: ${SINK}"
            break
        fi

        echo "$VC $FREQ_HZ $CURRENT_SSRC $CURRENT_PORT $PID" >> "$tmp_file"

        info "Started ${SINK} PID=${PID}"

        SSRC=$((SSRC + 1))
        PORT=$((PORT + 1))

    done

    if ! mv "$tmp_file" "$PID_FILE"; then
        error "Failed writing PIDs file"
        rm -f "$tmp_file"
        return 1
    fi

    if [[ $start_failed -ne 0 ]]; then
        warn "One or more streamers failed to start."

        return 1
    fi

    info "All ${GROUP_ID} VFO streamers started"
}


stop_streamers()
{
    if [[ ! -f "$PID_FILE" ]]; then
        info "No VFO PID file found"
        return
    fi

    if [[ ! -r "$PID_FILE" ]]; then
        error "Cannot read VFO PID file: $PID_FILE"
        exit 1
    fi

    if [[ ! -s "$PID_FILE" ]]; then
        rm -f "$PID_FILE"
        info "Empty VFO PID file removed"
        return
    fi


    info "Stopping ${GROUP_ID} VFO streamers..."


    while read -r VC FREQ_HZ SSRC PORT PID; do

        [[ -z "$PID" ]] && continue


        info "Stopping VC=${VC} PID=${PID}"


        if ! kill -0 "$PID" 2>/dev/null; then
            warn "PID ${PID} is not running"
            continue
        fi


        local CMDLINE

        CMDLINE=$(ps -p "$PID" -o cmd= || true)


        if [[ "$CMDLINE" != *"ka9q_vfo_streamer.py"* && "$CMDLINE" != *"ka9q-vfo-streamer"* ]]; then
            warn "PID ${PID} is not a ka9q streamer, leaving process untouched"
            continue
        fi


        kill "$PID"


        for i in {1..20}; do

            if ! kill -0 "$PID" 2>/dev/null; then
                break
            fi

            sleep 0.1

        done


        if kill -0 "$PID" 2>/dev/null; then

            warn "Force killing PID ${PID}"

            kill -9 "$PID"

        fi


    done < "$PID_FILE"


    rm -f "$PID_FILE"


    info "${GROUP_ID} VFO streamers stopped"
}



###############################################################################
# STATUS
###############################################################################

show_status()
{
    echo
    echo "==============================="
    echo " ${GROUP_ID} VFO STATUS"
    echo "==============================="


    echo
    echo "Virtual sinks:"

    if [[ -f "$MODULE_FILE" ]]; then

        while read -r SINK FREQ MODULE; do
            echo "  ${SINK} ${FREQ}Hz module=${MODULE}"
        done < "$MODULE_FILE"

    else

        echo "  None"

    fi



    echo
    echo "VFO streamers:"

    if [[ -f "$PID_FILE" ]]; then

        while read -r VC FREQ SSRC PORT PID; do

            if kill -0 "$PID" 2>/dev/null; then
                echo "  VC=${VC} ${FREQ}Hz PID=${PID} RUNNING"
            else
                echo "  VC=${VC} ${FREQ}Hz PID=${PID} STOPPED"
            fi

        done < "$PID_FILE"

    else

        echo "  None"

    fi

    echo
}



###############################################################################
# MAIN
###############################################################################

usage()
{
    echo
    echo "Usage:"
    echo
    echo "  $0 [-c|--config-dir DIR] list"
    echo "  $0 [-c|--config-dir DIR] <GROUP_ID> start"
    echo "  $0 [-c|--config-dir DIR] <GROUP_ID> stop"
    echo "  $0 [-c|--config-dir DIR] <GROUP_ID> restart"
    echo "  $0 [-c|--config-dir DIR] <GROUP_ID> status"
    echo
    echo "Example:"
    echo
    echo "  $0 list"
    echo "  $0 hf_aprs start"
    echo
}


main()
{
    parse_global_options "$@"

    echo "Config directory: [${STREAMER_CFG_DIR}]"

    validate_arguments "${REMAINING_ARGS[@]}"

    case "$ACTION" in

        list)

            list_groups
            ;;


        start|restart)

            check_runtime_requirements
            check_audio_requirements
            acquire_lock
            
            load_config

            stop_streamers
            unload_virtual_cards

            load_virtual_cards || {
                unload_virtual_cards
                exit 1
            }
            start_streamers || {
                stop_streamers
                unload_virtual_cards
                exit 1
            }
            ;;


        stop)

            check_audio_requirements
            acquire_lock

            load_config

            stop_streamers
            unload_virtual_cards
            ;;


        status)

            validate_group_config
            show_status
            ;;


        *)

            usage
            exit 1
            ;;

    esac
}


main "$@"