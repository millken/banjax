/*
 * Functions deal with the ip white listing.
 *
 * Copyright (c) eQualit.ie 2013 under GNU AGPL v3.0 or later
 *
 *  Vmon: Oct 2013, Initial version
 */
#include <string>
#include <list>

#include <ts/ts.h>

using namespace std;
#include "util.h"
#include "white_lister.h"

/**
  reads all the regular expressions from the database.
  and compile them
 */
void
WhiteLister::load_config()
{
  TSDebug(BANJAX_PLUGIN_NAME, "Loading white lister manager conf");
  try
  {
    YAML::Node white_listed_ips = cfg["white_listed_ips"];

    unsigned int count = white_listed_ips.size();

    for(unsigned int i = 0; i < count; i++) {
      SubnetRange cur_range = make_mask_for_range(white_listed_ips[i].as<std::string>());
      white_list.insert(cur_range);

      TSDebug(BANJAX_PLUGIN_NAME, "White listing ip range: %s as %x, %x",
          white_listed_ips[i].as<std::string>().c_str(),
          cur_range.first,
          cur_range.second);
    }
  }
  catch(std::exception& e)
  {
    TSDebug(BANJAX_PLUGIN_NAME, "Error loading white lister config: %s", e.what());
    throw;
  }

  TSDebug(BANJAX_PLUGIN_NAME, "Done loading white lister manager conf");
}

FilterResponse WhiteLister::on_http_request(const TransactionParts& transaction_parts)
{
  auto ip = transaction_parts.at(TransactionMuncher::IP);

  if (auto hit_range = white_list.is_white_listed(ip)) {
    TSDebug(BANJAX_PLUGIN_NAME, "white listed ip: %s in range %X",
        ip.c_str(),
        hit_range->first);

    return FilterResponse(FilterResponse::SERVE_IMMIDIATELY_DONT_CACHE);
  }

  return FilterResponse(FilterResponse::GO_AHEAD_NO_COMMENT);
}


