-- Define SpaceWire Protocol
local spacewire_proto = Proto("SpaceWire", "SpaceWire Protocol")

-- Define protocol fields
local f_src = ProtoField.uint8("spacewire.src", "Source Address", base.HEX)
local f_dst = ProtoField.uint8("spacewire.dst", "Destination Address", base.HEX)
local f_route = ProtoField.uint8("spacewire.route", "Route", base.HEX)
local f_data = ProtoField.string("spacewire.data", "Data")
local f_crc = ProtoField.uint8("spacewire.crc", "CRC", base.HEX)
local f_expected_crc = ProtoField.uint8("spacewire.expected_crc", "Expected CRC", base.HEX)

-- Register fields
spacewire_proto.fields = { f_src, f_dst, f_route, f_data, f_crc, f_expected_crc }

-- CRC Calculation Function (basic XOR CRC-8)
local function calc_crc8(data)
    local crc = 0
    for i = 0, data:len() - 1 do
        crc = bit.bxor(crc, data(i,1):uint())
    end
    return crc & 0xFF
end

-- Dissector function
function spacewire_proto.dissector(buffer, pinfo, tree)
    pinfo.cols.protocol = "SpaceWire"

    local subtree = tree:add(spacewire_proto, buffer(), "SpaceWire Packet")

    -- Extract fields
    local src = buffer(0,1)
    local dst = buffer(1,1)
    local route = buffer(2,1)
    local data_length = buffer:len() - 4
    local data = buffer(3, data_length)
    local crc_field = buffer(buffer:len()-1, 1)
    local crc_val = crc_field:uint()

    -- Calculate expected CRC
    local data_for_crc = buffer(0, buffer:len()-1)
    local expected_crc = calc_crc8(data_for_crc)

    -- Add fields to tree
    subtree:add(f_src, src)
    subtree:add(f_dst, dst)
    subtree:add(f_route, route)
    subtree:add(f_data, data)
    subtree:add(f_crc, crc_field)
    subtree:add(f_expected_crc, expected_crc)

    -- Info column
    if crc_val ~= expected_crc then
        pinfo.cols.info = string.format("CRC ERROR: Src %02X -> Dst %02X (Expected: %02X, Got: %02X)", src:uint(), dst:uint(), expected_crc, crc_val)
    else
        pinfo.cols.info = string.format("Valid Packet: Src %02X -> Dst %02X", src:uint(), dst:uint())
    end
end

-- Register the protocol for Ethernet frames (custom Ethertype)
local eth_table = DissectorTable.get("ethertype")
eth_table:add(0x88B5, spacewire_proto)
