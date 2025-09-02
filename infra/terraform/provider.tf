# terraform {
#   required_version = ">= 1.6.0"
#   required_providers {
#     oci = { source = "oracle/oci", version = ">= 6.0.0" }
#   }
# }

terraform {
  # loosen constraint to match local terraform (or upgrade terraform to match original constraint)
  required_version = ">= 1.5.0"

  required_providers {
    oci = {
      source  = "hashicorp/oci"
      version = ">= 4.0.0"
    }
  }
}

provider "oci" {
  config_file_profile = var.oci_profile
}


