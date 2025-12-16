{
  description = "python devshell with uv";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  inputs.nixpkgs-python.url = "github:cachix/nixpkgs-python";

  outputs =
    {
      self,
      nixpkgs,
      nixpkgs-python,
    }:
    let
      system = "x86_64-linux";
      pkgs = import nixpkgs { inherit system; };

      mkDevShell =
        version:
        pkgs.mkShell {
          buildInputs = [
            nixpkgs-python.packages.${system}."${version}"
            pkgs.uv
          ];
          shellHook = ''
            export LD_LIBRARY_PATH=${
              pkgs.lib.makeLibraryPath [
                pkgs.zlib
                pkgs.stdenv.cc.cc
              ]
            }:$LD_LIBRARY_PATH
          '';
        };
    in
    {
      devShells.${system} = rec {
        py38 = mkDevShell "3.8.17";
        py312 = mkDevShell "3.12.0";
      };
      devShell.${system} = self.devShells.${system}.py38;
    };
}
