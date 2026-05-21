local util = {}

local LibDeflate = require("LibDeflate")
local ieee754 = require("ieee754")

local prec = 1e-3
local prec2 = prec^2
util.prec = prec

local abs = math.abs

local max_parallel_angle = 1
local mpa_cos = math.cos(max_parallel_angle/360 * 2*math.pi)

-- compute epsilon real quick
local e = 1
while 1 + e ~= 1 do
	e = e * 0.5
end
util.e = e



function util.mod1_dec(x, m)
	return (x - 2) % m + 1
end

function util.mod1_inc(x, m)
	return x % m + 1
end

function util.bind(f, obj)
	return function(...)
		return f(obj, ...)
	end
end

function util.union_k(...)
	local r = {}
	for i, t in ipairs{...} do
		for k, v in next, t do
			r[k] = v
		end
	end
	return r
end

function util.union_i(...)
	local r = {}
	for j, t in ipairs{...} do
		for i, v in ipairs(t) do
			r[#r + 1] = v
		end
	end
	return r
end

function util.validate_bool(txt)
	txt = txt:lower()
	if txt == 'true' or txt == 't' then
		return true
	elseif txt == 'false' or txt == 'f' then
		return false
	end
end

function util.get_trace(msg)
	return msg .. '; ' .. debug.traceback()
end

function util.pcall(f, ...)
	return xpcall(f, util.get_trace, ...)
end

util.b2d = ieee754.bin2double

function util.b2i(b)
	local bytes = {b:byte(1, #b)}
	local x = 0
	for i = 4, 1, -1 do
		x = x * 256
		x = x + bytes[i]
	end



	return x
end

function util.b2i64(b)
	local bytes = {b:byte(1, #b)}
	local x = 0
	for i = 8, 1, -1 do
		x = x * 256
		x = x + bytes[i]
	end



	return x
end

function util.b2v(b)
	return Vector3.new(
		util.b2d(b:sub(1, 8)),
		util.b2d(b:sub(9, 16)),
		util.b2d(b:sub(17, 24))
	)
end

function util.read_i(s, i)
	return util.b2i(s:sub(i, i + 3)), i + 4
end

function util.read_i64(s, i)
	return util.b2i64(s:sub(i, i + 7)), i + 8
end

function util.read_d(s, i)
	return util.b2d(s:sub(i, i + 7)), i + 8
end

function util.read_v(s, i)
	return util.b2v(s:sub(i, i + 23)), i + 24
end

function util.read_t(s, i)
	return s:sub(i, i):byte(), i + 1
end

function util.read_s(s, i)
	local n
	n, i = util.read_i(s, i)
	local si = i
	i = i + n
	local str = s:sub(si, i - 1)

	return str, i
end

function util.read_a(s, i)
	local ty
	ty, i = util.read_t(s, i)
	if ty == 0 then

		return util.read_s(s, i)
	elseif ty == 1 then

		return util.read_d(s, i)
	else
		error('Received unknown field type: ' .. tostring(ty))
	end
end

function util.decode(value)
	return LibDeflate:DecompressDeflate(util.decode_zeros(value))
end

function util.decode_params(data, i)
	local fields = {}
	local n
	n, i = util.read_i(data, i)
	for j = 1, n do
		local name, value
		name, i = util.read_s(data, i)
		value, i = util.read_a(data, i)
		fields[name] = value
	end
	return fields, i
end

function util.load(data, i, format, context)
	if not format then
		return
	end
	
	-- custom types have a "format" property
	local class
	if format.format then
		class = format
		format = format.format
	end



	local obj
	if format == F.ID then
		obj = #context[#context] + 1
	elseif format.type then
		if format.type == 'compat' then
			obj, i = util.load(data, i, format.func(context), context)
		elseif format.type == 'ref' then
			local id
			id, i = util.read_i(data, i)
			obj = context[format.of][id]
		elseif format.type == 'konst' then
			if format.is_serialized then
				obj, i = util.load(data, i, format.v_format, context)
			else
				obj = format.value
			end
		elseif format.type == 'save' then
			obj, i = util.load(data, i, format.v_format, context)
			context[format.name] = obj
		elseif format.type == 'enable_if' then
			if format.cond(data, i, context) then
				obj, i = util.load(data, i, format.v_format, context)
			end
		elseif format.type == 'union' then
			obj = {}
			for j, v_format in ipairs(format) do
				context.obj = obj
				obj, i = util.load(data, i, v_format, context)
			end

		else
			obj = context.obj
			if obj then
				context.obj = nil
			else
				obj = {}
			end

			if format.key then
				context[format.key] = obj
			end
			if format.type == 'struct' then
				for j, field in ipairs(format.fields) do
					local k, v_format = next(field)

					obj[k], i = util.load(data, i, v_format, context)
				end
			elseif format.type == 'array' then
				local v_format = format.v_format
				for j = 1, format.len do
					obj[j], i = util.load(data, i, v_format, context)
				end
			else
				local n
				n, i = util.read_i(data, i)
				local stack_id = #context + 1
				context[stack_id] = obj
				if format.type == 'list' then
					local v_format = format.v_format
					for j = 1, n do
						obj[j], i = util.load(data, i, v_format, context)
					end
				elseif format.type == 'map' then
					local k_format = format.k_format
					local v_format = format.v_format
					for j = 1, n do
						local k, v
						k, i = util.load(data, i, k_format, context)
						if k ~= nil then
							v, i = util.load(data, i, v_format, context)
							obj[k] = v

						end
					end
				else
					print('unknown format type:', format.type)
				end
				context[stack_id] = nil
			end
		end
	end

	if class and class.MT then
		setmetatable(obj, class.MT)
	end

	if format.load then


		obj, i = format.load(obj, data, i, context)

	end

	return obj, i
end

util.d2b = ieee754.double2bin;

function util.a(to, str)
	to[#to + 1] = str
	if to.size then
		to.size = to.size + #str
	end
end

function util.i2b(x)
	local bytes = {nil, nil, nil, nil}
	for i = 1, 4 do
		local byte = x % 256
		x = (x - byte) / 256
		bytes[i] = byte
	end


	return string.char(table.unpack(bytes))

end

function util.i642b(x)
	local bytes = {nil, nil, nil, nil, nil, nil, nil, nil}
	for i = 1, 8 do
		local byte = x % 256
		x = (x - byte) / 256
		bytes[i] = byte
	end


	return string.char(table.unpack(bytes))

end

function util.v2b(v)
	local s = table.concat {
		util.d2b(v.X),
		util.d2b(v.Y),
		util.d2b(v.Z)
	}

	return s
end

function util.s2b(s)
	return util.i2b(#s) .. s
end

function util.a2b(v)
	local ty = type(v)
	if ty == 'string' then
		return string.char(0) .. util.s2b(v)
	elseif ty == 'number' then
		return string.char(1) .. util.d2b(v)
	end
end

function util.encode(value)
	return util.encode_zeros(LibDeflate:CompressDeflate(value, {level = 9}))
end

local special = string.char(255)
function util.encode_zeros(value)
	local data = {}
	local i = 1
	local n = #value
	while i <= n do
		local b = value:byte(i)
		if b == 0 then
			local m = 1
			while i < n and m < 254 do
				if value:byte(i + 1) == 0 then
					m = m + 1
					i = i + 1
				else
					break
				end
			end
			data[#data + 1] = special
			data[#data + 1] = string.char(m)
		elseif b == 255 then
			data[#data + 1] = special
			data[#data + 1] = special
		else
			data[#data + 1] = string.char(b)
		end
		i = i + 1
	end
	return table.concat(data)
end

local null = string.char(0)
function util.decode_zeros(value)
	local data = {}
	local i = 1
	local n = #value
	while i <= n do
		local b = value:byte(i)
		if b == 255 then
			i = i + 1
			b = value:byte(i)
			if b == 255 then
				data[#data + 1] = special
			else
				for j = 1, b do
					data[#data + 1] = null
				end
			end
		else
			data[#data + 1] = string.char(b)
		end
		i = i + 1
	end
	return table.concat(data)
end

function util.save(data, obj, format, context)
	if not format then
		return
	end

	-- custom types have a "format" property
	format = format.format or format



	if format.type then
		if format.type == 'compat' then
			util.save(data, obj, format.func(context), context)
		elseif format.type == 'ref' then
			a(data, util.i2b(obj.id))
		elseif format.type == 'konst' then
			if format.is_serialized then
				util.save(data, format.value, format.v_format, context)
			end
		elseif format.type == 'save' then
			util.save(data, obj, format.v_format, context)
			if format.v_format.type == 'konst' then
				context[format.name] = format.v_format.value
			else
				context[format.name] = obj
			end
		elseif format.type == 'enable_if' then
			util.save(data, obj, format.v_format, context)
		elseif format.type == 'union' then
			for j, v_format in ipairs(format) do
				util.save(data, obj, v_format, context)
			end
		elseif format.type == 'struct' then
			for j, field in ipairs(format.fields) do
				local k, v = next(field)

				util.save(data, obj[k], v, context)
			end
		elseif format.type == 'array' then
			local v_format = format.v_format
			for i = 1, format.len do
				util.save(data, obj[i], v_format, context)
			end
		else
			local i, n = #data + 1, 0
			data[i] = ''
			if format.type == 'list' then
				local v_format = format.v_format
				n = #obj
				for i, v in ipairs(obj) do
					util.save(data, v, v_format, context)
				end
			elseif format.type == 'map' then
				local k_format = format.k_format
				local v_format = format.v_format
				for k, v in next, obj do
					n = n + 1
					util.save(data, k, k_format, context)
					util.save(data, v, v_format, context)
				end
			else
				print('unknown format type:', format.type)
			end
			data[i] = util.i2b(n)
		end
	end

	if format.save then


		format.save(obj, data, context)
	end


end


return util