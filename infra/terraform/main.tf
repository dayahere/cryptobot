data "oci_identity_availability_domains" "ads" {
  compartment_id = var.compartment_ocid
}

resource "oci_core_virtual_network" "vcn" {
  compartment_id = var.compartment_ocid
  display_name   = "bot-vcn"
  cidr_block     = "10.0.0.0/16"
}

resource "oci_core_internet_gateway" "igw" {
  compartment_id = var.compartment_ocid
  display_name   = "bot-igw"
  vcn_id         = oci_core_virtual_network.vcn.id
}

resource "oci_core_route_table" "rt" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_virtual_network.vcn.id
  route_rules {
    network_entity_id = oci_core_internet_gateway.igw.id
    destination       = "0.0.0.0/0"
  }
}

resource "oci_core_subnet" "subnet" {
  compartment_id             = var.compartment_ocid
  vcn_id                     = oci_core_virtual_network.vcn.id
  display_name               = "bot-subnet"
  cidr_block                 = "10.0.1.0/24"
  route_table_id             = oci_core_route_table.rt.id
  prohibit_public_ip_on_vnic = false
}

resource "oci_core_network_security_group" "nsg" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_virtual_network.vcn.id
  display_name   = "bot-nsg"
}

resource "oci_core_network_security_group_security_rule" "allow_ssh" {
  network_security_group_id = oci_core_network_security_group.nsg.id
  direction                 = "INGRESS"
  protocol                  = "6"
  source                    = "0.0.0.0/0"
  tcp_options {
    destination_port_range {
      min = 3000
      max = 9093
    }
  }
}

resource "oci_core_network_security_group_security_rule" "allow_observability" {
  network_security_group_id = oci_core_network_security_group.nsg.id
  direction                 = "INGRESS"
  protocol                  = "6"
  source                    = "0.0.0.0/0"
  tcp_options {
    destination_port_range {
      min = 3000
      max = 9093
    }
  }
}

locals {
  cloud_init = file("/cloud-init.yaml")
}

resource "oci_core_instance" "bot_vm" {
  availability_domain = data.oci_identity_availability_domains.ads.availability_domains[0].name
  compartment_id      = var.compartment_ocid
  display_name        = "crypto-bot-a1"
  shape               = "VM.Standard.A1.Flex"
  shape_config {
    ocpus         = 2
    memory_in_gbs = 12
  }
  create_vnic_details {
    subnet_id        = oci_core_subnet.subnet.id
    assign_public_ip = true
    nsg_ids          = [oci_core_network_security_group.nsg.id]
  }
  metadata = {
    ssh_authorized_keys = file(var.ssh_public_key_path)
    user_data           = base64encode(templatefile("/cloud-init.yaml", { repo_url = var.repo_url }))
  }
}


