-- SpaceFibre Wireshark Lua Dissector

-- Protocol Registration
local p_spacefibre = Proto("spacefibre", "SpaceFibre Protocol")

-- Unique Fields
local f_sf_src = ProtoField.uint8("spacefibre.src", "Source Address", base.DEC)
local f_sf_dst = ProtoField.uint8("spacefibre.dst", "Destination Address", base.DEC)
local f_sf_vc = ProtoField.uint8("spacefibre.vc", "Virtual Channel", base.DEC)
local f_sf_seq = ProtoField.uint8("spacefibre.seq_num", "Sequence Number", base.DEC)
local f_sf_fc = ProtoField.uint8("spacefibre.flow_control", "Flow Control", base.DEC, {
    [0] = "Normal",
    [1] = "Pause"
})
local f_sf_data = ProtoField.bytes("spacefibre.data", "Data")
local f_sf_crc = ProtoField.uint8("spacefibre.crc", "CRC", base.HEX)

-- Register fields to the protocol
p_spacefibre.fields = {
    f_sf_src, f_sf_dst, f_sf_vc, f_sf_seq, f_sf_fc, f_sf_data, f_sf_crc
}

-- Dissector function
function p_spacefibre.dissector(buffer, pinfo, tree)
    if buffer:len() < 7 then return end -- Minimum length check

    pinfo.cols.protocol = "SpaceFibre"

    local subtree = tree:add(p_spacefibre, buffer(), "SpaceFibre Protocol Data")
    local offset = 0

    subtree:add(f_sf_src, buffer(offset, 1)); offset = offset + 1
    subtree:add(f_sf_dst, buffer(offset, 1)); offset = offset + 1
    subtree:add(f_sf_vc, buffer(offset, 1)); offset = offset + 1
    subtree:add(f_sf_seq, buffer(offset, 1)); offset = offset + 1
    subtree:add(f_sf_fc, buffer(offset, 1)); offset = offset + 1

    local data_len = buffer:len() - offset - 1
    if data_len > 0 then
        subtree:add(f_sf_data, buffer(offset, data_len))
        offset = offset + data_len
    end

    subtree:add(f_sf_crc, buffer(offset, 1))

    -- Display short info
    pinfo.cols.info = string.format(
        "SF VC:%d Seq:%d From:%d To:%d",
        buffer(2,1):uint(), buffer(3,1):uint(), buffer(0,1):uint(), buffer(1,1):uint()
    )
end

-- Register protocol to a different EtherType (so it doesn’t conflict with SpaceWire)
local ethertype_table = DissectorTable.get("ethertype")
ethertype_table:add(0x88B6, p_spacefibre) -- 0x88B6 = Custom EtherType for SpaceFibre
