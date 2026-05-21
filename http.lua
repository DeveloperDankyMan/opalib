-- Polaris-Nav, advanced pathfinding as a library and service
-- Copyright (C) 2021 Tyler R. Herman-Hoyer
-- tyler@hoyerz.com
--
-- This program is free software; you can redistribute it and/or
-- modify it under the terms of the GNU Lesser General Public
-- License as published by the Free Software Foundation; either
-- version 3 of the License, or (at your option) any later version.
--
-- This program is distributed in the hope that it will be useful,
-- but WITHOUT ANY WARRANTY; without even the implied warranty of
-- MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
-- Lesser General Public License for more details.
--
-- You should have received a copy of the GNU General Public License
-- along with this program. If not, see <https://www.gnu.org/licenses/>.

local e = _G

local http = game:GetService 'HttpService'

local api = {}

local timeout = 120
local inf = math.huge

local ERR_TIMED_OUT = 'Request timed out at %d seconds.'
local ERR_LATE = 'Response arrived late (after %d seconds).'
local ERR_HTTP = 'Request received HTTP %d %s "%s"'
local ERR_RBX = 'Request received an error: "%s"'

local LL = {}
LL.prev = LL
LL.next = LL

local Request = {}

-- Default error handler. May be called multiple times as errors happen.
function Request:default_throw(args)
	-- Emit if late
	if not self.is_active then
		local flight_time = self.finish_t - self.start_t
		if self.success == nil then
			e.warn(ERR_TIMED_OUT:format(flight_time))
		else
			e.warn(ERR_LATE:format(flight_time))
		end
	end

	-- Emit if there was an error response
	local r = self.response
	if self.success then
		-- lua error after request completed
		if r.Success then
			e.warn(self.msg)
		-- HTTP network error
		elseif r.StatusCode == 401 and r.Body == "Session has expired" then
			local auth = e.store:getState().auth
			return api.refresh {
				token = auth.token;
				id = auth.UserId;
				session = auth.session;
			}:Then(function (p, session)
				e.set_session {
					session = session;
				}
				self.predecessor.args.Headers.session = session
				self:Stop()
				return self.predecessor:RepeatAsync()
			end)
		else
			warn(ERR_HTTP:format(
				r.StatusCode,
				r.StatusMessage,
				r.Body
			))
		end
	-- Roblox network error
	elseif self.success == false then
		e.warn(ERR_RBX:format(r))

	-- lua errors before request was sent
	else
		e.warn(self.msg)
	end

	-- Emit where the request was made
	print(self.traceback)

	-- Continue additional error handlers
	return self:Continue(args, self.msg)
end

-- Sends a request and waits for the response
function Request:exec()
	-- enqueue the request
	self.next = LL
	self.prev = LL.prev
	self.next.prev = self
	self.prev.next = self

	-- send the request
	self.start_t = tick()

	self.success, self.response = pcall(http.RequestAsync, http, self.args)
	self.finish_t = tick()



	if self.is_active then
		self.prev.next = self.next
		self.next.prev = self.prev
	elseif not self.args.accept_late then
		return self:Throw()
	end

	if self.success and self.response.Success then
		return self:Continue()
	else
		return self:Throw()
	end
end

-- Create, enqueue, and send a new request
function api.req(args)
	local req = setmetatable({
		promise = nil;
		success = nil;
		response = nil;
		args = args;
		next = nil;
		prev = nil;
		start_t = inf;
		is_active = true;
		traceback = debug.traceback(nil, 2);
	}, Request)

	-- Promise for handling errors / responses
	req.promise = e.promise(req)
	:Silent()
	:Then(Request.exec)
	:Else(Request.default_throw)

	return req.promise
end

-- Event loop for timing out requests
task.spawn(function()
	while true do
		local t = tick()
		local cur = LL.next
		while cur ~= LL and t - cur.start_t > timeout do
			cur.is_active = false
			cur.promise:ThrowAsync()
			cur = cur.next
		end
		LL.next = cur
		cur.prev = LL

		wait()
	end
end)

return api