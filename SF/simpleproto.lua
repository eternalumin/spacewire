-- Define a new protocol
simple_proto = Proto("SimpleProto", "Simple Protocol")

-- Define protocol fields
simple_proto.fields.packet_id = ProtoField.uint16("simpleproto.packet_id", "Packet ID", base.DEC)
simple_proto.fields.length = ProtoField.uint8("simpleproto.length", "Payload Length", base.DEC)
simple_proto.fields.payload = ProtoField.string("simpleproto.payload", "Payload Data")

-- Dissector function
function simple_proto.dissector(buffer, pinfo, tree)
    if buffer:len() < 3 then return end  -- Minimum 3 bytes required

    pinfo.cols.protocol = "SimpleProto"

    -- Create the protocol tree
    local subtree = tree:add(simple_proto, buffer(), "SimpleProto Packet")

    -- Extract fields
    local packet_id = buffer(0,2):uint()
    local length = buffer(2,1):uint()
    local payload = buffer(3):string()

    -- Add fields to tree
    subtree:add(simple_proto.fields.packet_id, buffer(0,2)):append_text(" (ID: " .. packet_id .. ")")
    subtree:add(simple_proto.fields.length, buffer(2,1)):append_text(" (Payload Length: " .. length .. ")")
    subtree:add(simple_proto.fields.payload, buffer(3)):append_text(" (Data: " .. payload .. ")")

    -- Update info column
    pinfo.cols.info = string.format("SimpleProto [ID: %d, Length: %d]", packet_id, length)
end

-- Register dissector for a specific port (example: UDP 5000)
DissectorTable.get("udp.port"):add(5000, simple_proto)
